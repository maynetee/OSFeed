import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_user
from app.config import get_settings
from app.database import get_db
from app.models.digest_preference import DigestPreference
from app.models.user import User
from app.schemas.digest import DigestPreferenceResponse, DigestPreferenceUpdate, DigestPreviewRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/preferences", response_model=DigestPreferenceResponse)
async def get_digest_preferences(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's digest preferences. Creates default if none exist."""
    result = await db.execute(
        select(DigestPreference).where(DigestPreference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = DigestPreference(user_id=user.id)
        db.add(pref)
        await db.flush()
        await db.refresh(pref)
    return pref


@router.post("/preferences", response_model=DigestPreferenceResponse)
async def update_digest_preferences(
    payload: DigestPreferenceUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's digest preferences."""
    result = await db.execute(
        select(DigestPreference).where(DigestPreference.user_id == user.id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = DigestPreference(user_id=user.id)
        db.add(pref)
        await db.flush()

    data = payload.model_dump(exclude_unset=True)

    if "send_hour" in data and not (0 <= data["send_hour"] <= 23):
        raise HTTPException(status_code=400, detail="send_hour must be between 0 and 23")
    if "max_messages" in data and data["max_messages"] not in (10, 20, 50):
        raise HTTPException(status_code=400, detail="max_messages must be 10, 20, or 50")
    if "frequency" in data and data["frequency"] not in ("daily", "weekly"):
        raise HTTPException(status_code=400, detail="frequency must be 'daily' or 'weekly'")

    for key, value in data.items():
        setattr(pref, key, value)

    await db.flush()
    await db.refresh(pref)
    return pref


@router.post("/preview")
async def send_digest_preview(
    payload: DigestPreviewRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a preview digest email to the current user."""
    from app.services.digest_service import build_digest_content, send_digest_email

    if not user.email:
        raise HTTPException(status_code=400, detail="No email address on your account")

    try:
        content = await build_digest_content(
            user=user,
            collection_ids=payload.collection_ids,
            max_messages=payload.max_messages or 20,
            session=db,
        )
        if not content["collections"]:
            raise HTTPException(status_code=404, detail="No messages found for the selected collections")

        success = await send_digest_email(user=user, content=content)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send digest email")

        return {"message": "Preview digest sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send digest preview for user {user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate digest preview")


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_digest(token: str, db: AsyncSession = Depends(get_db)):
    """One-click unsubscribe from digest emails. No auth required."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("purpose") != "digest_unsubscribe":
            raise HTTPException(status_code=400, detail="Invalid token")
        user_id = payload["sub"]
    except jwt.ExpiredSignatureError:
        return HTMLResponse(
            content="<html><body><h1>Link Expired</h1>"
            "<p>This unsubscribe link has expired. Please visit your settings page to manage digest preferences.</p>"
            "</body></html>"
        )
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid token")

    result = await db.execute(
        select(DigestPreference).where(DigestPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    if pref:
        pref.enabled = False
        await db.commit()

    return HTMLResponse(
        content="<html><body><h1>Unsubscribed</h1>"
        "<p>You have been unsubscribed from OSFeed daily digests. "
        "You can re-enable them anytime from your settings.</p>"
        "</body></html>"
    )
