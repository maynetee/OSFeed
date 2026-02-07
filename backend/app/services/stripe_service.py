import stripe
from app.config import get_settings


async def create_checkout_session(
    user_id: str,
    user_email: str,
    plan: str,
    billing: str,
    success_url: str,
    cancel_url: str,
):
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    price_map = {
        ("solo", "monthly"): settings.stripe_solo_monthly_price_id,
        ("solo", "yearly"): settings.stripe_solo_yearly_price_id,
        ("team", "monthly"): settings.stripe_team_monthly_price_id,
        ("team", "yearly"): settings.stripe_team_yearly_price_id,
    }
    price_id = price_map.get((plan, billing))
    if not price_id:
        raise ValueError(f"Invalid plan/billing combination: {plan}/{billing}")

    session = stripe.checkout.Session.create(
        customer_email=user_email,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user_id, "plan": plan},
    )
    return session


async def create_portal_session(customer_id: str, return_url: str):
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session
