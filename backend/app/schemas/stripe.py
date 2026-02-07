from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    plan: str  # "solo" or "team"
    billing: str  # "monthly" or "yearly"


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str
