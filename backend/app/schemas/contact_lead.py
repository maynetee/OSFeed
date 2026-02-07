from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ContactSalesCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company: str = Field(..., min_length=2, max_length=100)
    job_title: str = Field(..., min_length=2, max_length=100)
    company_size: str = Field(..., pattern=r"^(1-10|11-50|51-200|201-500|500\+)$")
    message: str | None = Field(None, max_length=2000)


class ContactSalesRead(BaseModel):
    id: UUID
    name: str
    email: str
    company: str
    job_title: str
    company_size: str
    message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
