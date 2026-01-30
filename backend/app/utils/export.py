"""Export utilities for CSV, HTML, and PDF generation."""
import csv
from html import escape
from io import StringIO, BytesIO
from typing import Any, Optional

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


# Standard CSV columns for message exports
MESSAGE_CSV_COLUMNS = [
    "message_id",
    "channel_title",
    "channel_username",
    "published_at",
    "original_text",
    "translated_text",
    "source_language",
    "target_language",
    "is_duplicate",
]


def create_csv_writer(output: Optional[StringIO] = None) -> tuple[csv.writer, StringIO]:
    """Create a CSV writer with a StringIO buffer.

    Args:
        output: Optional StringIO buffer. If None, a new one is created.

    Returns:
        tuple: (csv.writer, StringIO) - The writer and its buffer.
    """
    if output is None:
        output = StringIO()
    writer = csv.writer(output)
    return writer, output


def generate_csv_row(message: Any, channel: Any) -> list:
    """Generate a standard CSV row for a message.

    Args:
        message: Message object with attributes: id, published_at, original_text,
                 translated_text, source_language, target_language, is_duplicate
        channel: Channel object with attributes: title, username

    Returns:
        list: Row data ready for csv.writer.writerow()
    """
    return [
        str(message.id),
        channel.title,
        channel.username,
        message.published_at,
        message.original_text or "",
        message.translated_text or "",
        message.source_language or "",
        message.target_language or "",
        message.is_duplicate,
    ]


def generate_html_template(title: str = "OSFeed - Messages") -> str:
    """Generate the HTML template header with styles.

    Args:
        title: Page title for the HTML document

    Returns:
        str: HTML template header including DOCTYPE, head, and opening body tag
    """
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        f"<title>{escape(title)}</title>"
        "<style>body{font-family:Arial,sans-serif;background:#f8fafc;color:#0f172a;padding:24px;}"
        "h1{font-size:20px;}article{margin:16px 0;padding:12px;border:1px solid #e2e8f0;"
        "border-radius:12px;background:#fff;}small{color:#64748b;}</style></head><body>"
    )


def generate_html_article(message: Any, channel: Any) -> str:
    """Generate an HTML article block for a message.

    Args:
        message: Message object with attributes: published_at, original_text,
                 translated_text
        channel: Channel object with attributes: title, username

    Returns:
        str: HTML article block with message content
    """
    parts = [
        "<article>",
        f"<small>{escape(channel.title)} · {escape(channel.username)} · {message.published_at}</small>",
        f"<p>{escape(message.translated_text or message.original_text or '')}</p>",
    ]

    if message.translated_text and message.original_text:
        parts.append(f"<p><small>Original: {escape(message.original_text)}</small></p>")

    parts.append("</article>")
    return "".join(parts)


def generate_pdf_bytes(html_content: str) -> bytes:
    """Generate PDF bytes from HTML content.

    Args:
        html_content: Complete HTML document string

    Returns:
        bytes: PDF file content as bytes

    Raises:
        RuntimeError: If weasyprint is not available
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "weasyprint is not installed. Install it with: pip install weasyprint"
        )

    pdf_buffer = BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
