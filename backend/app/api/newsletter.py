import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.newsletter_subscriber import NewsletterSubscriber
from app.schemas.newsletter import NewsletterSubscribeRequest, NewsletterSubscribeResponse
from app.services.email_service import email_service, _redact_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/newsletter", tags=["newsletter"])


@router.post("/subscribe", response_model=NewsletterSubscribeResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(data: NewsletterSubscribeRequest, db: AsyncSession = Depends(get_db)):
    """Subscribe to the OSFeed newsletter. No authentication required."""
    try:
        # Check if already subscribed
        result = await db.execute(
            select(NewsletterSubscriber).where(NewsletterSubscriber.email == data.email)
        )
        existing = result.scalars().first()

        if existing:
            if existing.is_active:
                return NewsletterSubscribeResponse(
                    message="You're already subscribed!",
                    email=data.email,
                )
            # Reactivate
            existing.is_active = True
            existing.unsubscribed_at = None
            existing.subscribed_at = datetime.now(timezone.utc)
            await db.flush()
        else:
            subscriber = NewsletterSubscriber(email=data.email)
            db.add(subscriber)
            await db.flush()

        logger.info(f"Newsletter subscription for {_redact_email(data.email)}")

        # Send welcome email in background
        try:
            asyncio.create_task(email_service.send_newsletter_welcome(data.email))
        except RuntimeError:
            logger.warning(f"Could not create newsletter welcome email task for {_redact_email(data.email)}")

        return NewsletterSubscribeResponse(
            message="Successfully subscribed to the newsletter!",
            email=data.email,
        )
    except SQLAlchemyError as e:
        logger.error(f"Failed to subscribe {_redact_email(data.email)}: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process subscription",
        )


@router.post("/unsubscribe")
async def unsubscribe(data: NewsletterSubscribeRequest, db: AsyncSession = Depends(get_db)):
    """Unsubscribe from the OSFeed newsletter."""
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == data.email)
    )
    subscriber = result.scalars().first()

    if not subscriber or not subscriber.is_active:
        return {"message": "Email not found or already unsubscribed."}

    subscriber.is_active = False
    subscriber.unsubscribed_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(f"Newsletter unsubscribe for {_redact_email(data.email)}")
    return {"message": "Successfully unsubscribed from the newsletter."}
