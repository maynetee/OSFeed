from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class NewsletterSubscribeRequest(BaseModel):
    email: EmailStr


class NewsletterSubscribeResponse(BaseModel):
    message: str
    email: str


class NewsletterSubscriberRead(BaseModel):
    id: UUID
    email: str
    subscribed_at: datetime
    is_active: bool
    unsubscribed_at: datetime | None

    model_config = {"from_attributes": True}
