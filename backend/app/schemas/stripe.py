from typing import Optional

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    plan: str  # "solo" or "team"
    billing: str  # "monthly" or "yearly"


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class CancelRequest(BaseModel):
    immediate: bool = False


class SubscriptionStatusResponse(BaseModel):
    plan: str
    status: str
    period_end: Optional[str] = None
    created_at: Optional[str] = None
    is_refund_eligible: bool = False


class CancelResponse(BaseModel):
    status: str
    period_end: Optional[str] = None
    message: str


class RefundResponse(BaseModel):
    status: str
    amount: Optional[int] = None
    currency: Optional[str] = None
    message: str
