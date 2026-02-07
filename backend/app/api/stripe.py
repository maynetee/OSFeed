"""Stripe payment API routes for OSFeed."""
import logging
from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.config import get_settings
from app.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.schemas.stripe import CheckoutRequest, CheckoutResponse, PortalResponse
from app.services.stripe_service import create_checkout_session, create_portal_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    user: User = Depends(current_active_user),
):
    settings = get_settings()
    success_url = f"{settings.frontend_url}/dashboard?checkout=success"
    cancel_url = f"{settings.frontend_url}/pricing?checkout=canceled"

    try:
        session = await create_checkout_session(
            user_id=str(user.id),
            user_email=user.email,
            plan=body.plan,
            billing=body.billing,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return CheckoutResponse(url=session.url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except stripe.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service temporarily unavailable",
        )


@router.post("/customer-portal", response_model=PortalResponse)
async def customer_portal(
    user: User = Depends(current_active_user),
):
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )

    settings = get_settings()
    return_url = f"{settings.frontend_url}/settings"

    try:
        session = await create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=return_url,
        )
        return PortalResponse(url=session.url)
    except stripe.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment service temporarily unavailable",
        )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    settings = get_settings()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    async with AsyncSessionLocal() as db:
        try:
            if event_type == "checkout.session.completed":
                await _handle_checkout_completed(db, data)
            elif event_type == "customer.subscription.updated":
                await _handle_subscription_updated(db, data)
            elif event_type == "customer.subscription.deleted":
                await _handle_subscription_deleted(db, data)
            else:
                logger.info(f"Unhandled Stripe event: {event_type}")

            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error handling Stripe webhook {event_type}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing failed")

    return JSONResponse(content={"status": "ok"})


async def _handle_checkout_completed(db: AsyncSession, session_data: dict):
    user_id = session_data.get("metadata", {}).get("user_id")
    plan = session_data.get("metadata", {}).get("plan")
    customer_id = session_data.get("customer")
    subscription_id = session_data.get("subscription")

    if not user_id:
        logger.warning("checkout.session.completed missing user_id in metadata")
        return

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"checkout.session.completed: user {user_id} not found")
        return

    user.stripe_customer_id = customer_id
    user.stripe_subscription_id = subscription_id
    user.subscription_plan = plan or "solo"
    user.subscription_status = "active"
    logger.info(f"Subscription activated for user {user_id}: plan={plan}")


async def _handle_subscription_updated(db: AsyncSession, subscription_data: dict):
    customer_id = subscription_data.get("customer")
    if not customer_id:
        return

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"subscription.updated: customer {customer_id} not found")
        return

    user.subscription_status = subscription_data.get("status", user.subscription_status)

    period_end = subscription_data.get("current_period_end")
    if period_end:
        user.subscription_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    logger.info(f"Subscription updated for customer {customer_id}: status={user.subscription_status}")


async def _handle_subscription_deleted(db: AsyncSession, subscription_data: dict):
    customer_id = subscription_data.get("customer")
    if not customer_id:
        return

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        logger.warning(f"subscription.deleted: customer {customer_id} not found")
        return

    user.subscription_status = "canceled"
    logger.info(f"Subscription canceled for customer {customer_id}")
