from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from io import BytesIO
from fpdf import FPDF

from app.database import get_db
from app.models.summary import Summary
from app.models.user import User
from app.schemas.summary import SummaryResponse, SummaryGenerateRequest, SummaryListResponse
from app.services.summarizer import generate_daily_summary
from app.auth.users import current_active_user
from app.services.audit import record_audit_event

router = APIRouter()


def _render_summary_pdf(summary: Summary) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    title = summary.title or "Daily Digest"
    pdf.multi_cell(0, 10, title)
    pdf.ln(2)
    pdf.set_font("Helvetica", size=12)
    for line in (summary.content or "").splitlines():
        pdf.multi_cell(0, 8, line)
    output = pdf.output(dest="S")
    if isinstance(output, str):
        return output.encode("latin-1", errors="ignore")
    return output


@router.get("/daily", response_model=SummaryResponse)
async def get_daily_summary(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest daily summary.

    Requires authentication.
    """
    result = await db.execute(
        select(Summary)
        .where(Summary.digest_type == "daily")
        .where(Summary.user_id == user.id)
        .order_by(desc(Summary.generated_at))
        .limit(1)
    )
    summary = result.scalar_one_or_none()

    if not summary:
        raise HTTPException(status_code=404, detail="No daily summary found")

    return summary


@router.get("", response_model=SummaryListResponse)
async def list_summaries(
    digest_type: str = "daily",
    limit: int = 10,
    offset: int = 0,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List summaries with pagination.

    Requires authentication.
    """
    query = (
        select(Summary)
        .where(Summary.user_id == user.id)
        .where(Summary.digest_type == digest_type)
        .order_by(desc(Summary.generated_at))
    )
    count_query = (
        select(func.count())
        .select_from(Summary)
        .where(Summary.user_id == user.id)
        .where(Summary.digest_type == digest_type)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.limit(limit).offset(offset))
    summaries = result.scalars().all()

    return SummaryListResponse(
        summaries=summaries,
        total=total,
        page=offset // limit + 1,
        page_size=limit,
    )


@router.post("/generate", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryGenerateRequest,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger summary generation.

    Requires authentication.
    """
    if request.digest_type == "daily":
        summary = await generate_daily_summary(db, user_id=user.id, filters=request.filters)
        record_audit_event(
            db,
            user_id=user.id,
            action="summary.generate",
            resource_type="summary",
            resource_id=str(summary.id),
        )
        await db.commit()
        return summary
    else:
        raise HTTPException(status_code=400, detail="Unsupported summary type")


@router.get("/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Summary).where(Summary.id == summary_id))
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    if summary.user_id and summary.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this summary")
    return summary


@router.get("/{summary_id}/export/html")
async def export_summary_html(
    summary_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Summary).where(Summary.id == summary_id))
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    if summary.user_id and summary.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this summary")
    return HTMLResponse(content=summary.content_html or summary.content or "")


@router.get("/{summary_id}/export/pdf")
async def export_summary_pdf(
    summary_id: str,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Summary).where(Summary.id == summary_id))
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    if summary.user_id and summary.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this summary")

    pdf_bytes = _render_summary_pdf(summary)
    filename = f"telescope-summary-{summary_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
