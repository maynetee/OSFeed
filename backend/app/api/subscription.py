"""Subscription management API routes (cancel, refund, status)."""
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.database import get_db
from app.models.user import User
from app.schemas.stripe import (
    CancelRequest,
    CancelResponse,
    RefundResponse,
    SubscriptionStatusResponse,
)
from app.services.email_service import email_service
from app.services.stripe_service import (
    cancel_subscription,
    create_refund,
    get_subscription_details,
)

logger = logging.getLogger(__name__)
router = APIRouter()

REFUND_ELIGIBILITY_DAYS = 14


@router.get("/status", response_model=SubscriptionStatusResponse)
async def subscription_status(
    user: User = Depends(current_active_user),
):
    """Get current subscription status and refund eligibility."""
    if not user.stripe_subscription_id:
        return SubscriptionStatusResponse(
            plan=user.subscription_plan or "none",
            status=user.subscription_status or "none",
            is_refund_eligible=False,
        )

    try:
        sub = await get_subscription_details(user.stripe_subscription_id)
    except stripe.StripeError as e:
        logger.error(f"Failed to retrieve subscription for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service temporarily unavailable",
        )

    created_at = datetime.fromtimestamp(sub.created, tz=timezone.utc)
    period_end = datetime.fromtimestamp(sub.current_period_end, tz=timezone.utc) if sub.current_period_end else None
    days_since_creation = (datetime.now(timezone.utc) - created_at).days

    return SubscriptionStatusResponse(
        plan=user.subscription_plan or "none",
        status=sub.status,
        period_end=period_end.isoformat() if period_end else None,
        created_at=created_at.isoformat(),
        is_refund_eligible=days_since_creation < REFUND_ELIGIBILITY_DAYS and sub.status == "active",
    )


@router.post("/cancel", response_model=CancelResponse)
async def cancel(
    body: CancelRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel subscription (end of period or immediately)."""
    if not user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )

    if user.subscription_status == "canceled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already canceled",
        )

    try:
        result = await cancel_subscription(user.stripe_subscription_id, immediate=body.immediate)
    except stripe.StripeError as e:
        logger.error(f"Failed to cancel subscription for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service temporarily unavailable",
        )

    if body.immediate:
        user.subscription_status = "canceled"
        period_end_str = None
        message = "Your subscription has been canceled immediately."
        access_until = None
    else:
        user.subscription_status = "cancel_at_period_end"
        period_end = (
            datetime.fromtimestamp(result.current_period_end, tz=timezone.utc) if result.current_period_end else None
        )
        period_end_str = period_end.isoformat() if period_end else None
        user.subscription_period_end = period_end
        message = "Your subscription will be canceled at the end of the billing period."
        access_until = period_end.strftime("%B %d, %Y") if period_end else None

    await db.commit()

    # Send cancellation email (non-blocking)
    try:
        await email_service.send_subscription_canceled(
            email=user.email,
            plan=user.subscription_plan or "none",
            effective_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            access_until=access_until,
        )
    except Exception as e:
        logger.error(f"Failed to send cancellation email to user {user.id}: {e}")

    return CancelResponse(
        status=user.subscription_status,
        period_end=period_end_str,
        message=message,
    )


@router.post("/refund", response_model=RefundResponse)
async def refund(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Request a full refund (only within 14 days of subscription creation)."""
    if not user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )

    if user.subscription_status == "canceled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already canceled",
        )

    # Check refund eligibility
    try:
        sub = await get_subscription_details(user.stripe_subscription_id)
    except stripe.StripeError as e:
        logger.error(f"Failed to retrieve subscription for refund check, user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service temporarily unavailable",
        )

    created_at = datetime.fromtimestamp(sub.created, tz=timezone.utc)
    days_since_creation = (datetime.now(timezone.utc) - created_at).days

    if days_since_creation >= REFUND_ELIGIBILITY_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Refund is only available within {REFUND_ELIGIBILITY_DAYS} days of subscription. "
            f"Your subscription was created {days_since_creation} days ago.",
        )

    # Process refund
    try:
        refund_result = await create_refund(user.stripe_subscription_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except stripe.StripeError as e:
        logger.error(f"Failed to process refund for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service temporarily unavailable",
        )

    # Update user model
    user.subscription_status = "canceled"
    user.stripe_subscription_id = None
    await db.commit()

    amount = refund_result.amount
    currency = refund_result.currency

    # Send refund confirmation email (non-blocking)
    try:
        refund_display = f"{amount / 100:.2f} {currency.upper()}" if amount and currency else None
        await email_service.send_subscription_canceled(
            email=user.email,
            plan=user.subscription_plan or "none",
            effective_date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            refund_amount=refund_display,
        )
    except Exception as e:
        logger.error(f"Failed to send refund email to user {user.id}: {e}")

    return RefundResponse(
        status="refunded",
        amount=amount,
        currency=currency,
        message="Your refund has been processed. It may take 5-10 business days to appear on your statement.",
    )
