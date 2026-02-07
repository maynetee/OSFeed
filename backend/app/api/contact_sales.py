import asyncio
import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.contact_lead import ContactSalesLead
from app.schemas.contact_lead import ContactSalesCreate
from app.services.email_service import email_service, _redact_email

logger = logging.getLogger(__name__)

router = APIRouter(tags=["contact-sales"])


@router.post("/contact-sales", status_code=status.HTTP_201_CREATED)
async def create_contact_lead(data: ContactSalesCreate, db: AsyncSession = Depends(get_db)):
    """Submit a contact sales inquiry. No authentication required."""
    try:
        lead = ContactSalesLead(
            name=data.name,
            email=data.email,
            company=data.company,
            job_title=data.job_title,
            company_size=data.company_size,
            message=data.message,
        )
        db.add(lead)
        await db.flush()
        logger.info(f"New contact sales lead from {data.company}")

        # Send confirmation email in background
        try:
            asyncio.create_task(email_service.send_contact_confirmation(data.email, data.name))
        except RuntimeError:
            logger.warning(f"Could not create contact confirmation email task for {_redact_email(data.email)}")

        return {"message": "Thank you! We'll get back to you within 24 hours."}
    except SQLAlchemyError as e:
        logger.error(f"Failed to save contact lead: {type(e).__name__}: {e}")
        raise
