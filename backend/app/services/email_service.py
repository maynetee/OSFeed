"""Email service with template rendering and provider abstraction."""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import get_settings

logger = logging.getLogger(__name__)

# Template setup - load from backend/app/templates/emails/
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "emails"


class TemplateRenderer:
    """Jinja2 template renderer for email templates."""

    def __init__(self):
        self._env: Optional[Environment] = None

    def _get_env(self) -> Environment:
        """Lazy load the Jinja2 environment."""
        if self._env is None:
            if TEMPLATE_DIR.exists():
                self._env = Environment(
                    loader=FileSystemLoader(str(TEMPLATE_DIR)),
                    autoescape=select_autoescape(['html', 'xml']),
                )
            else:
                logger.warning(f"Email template directory not found: {TEMPLATE_DIR}")
                self._env = Environment(autoescape=select_autoescape(['html', 'xml']))
        return self._env

    def render(self, template_name: str, **context) -> str:
        """Render a template with the given context."""
        try:
            template = self._get_env().get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            # Return a simple fallback
            return f"Error rendering email template: {template_name}"


template_renderer = TemplateRenderer()


class EmailProvider(ABC):
    """Abstract base class for email providers."""

    @abstractmethod
    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        """Send an email. Returns True if successful."""
        pass


class SMTPProvider(EmailProvider):
    """SMTP email provider using aiosmtplib."""

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        """Send email via SMTP using aiosmtplib."""
        settings = get_settings()
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
            msg["To"] = to

            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user if settings.smtp_user else None,
                password=settings.smtp_password if settings.smtp_password else None,
                start_tls=settings.smtp_use_tls,
            )
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


class ResendProvider(EmailProvider):
    """Resend API email provider."""

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        """Send email via Resend API."""
        settings = get_settings()
        try:
            import resend
            resend.api_key = settings.resend_api_key

            resend.Emails.send({
                "from": f"{settings.email_from_name} <{settings.email_from_address}>",
                "to": to,
                "subject": subject,
                "html": html,
                "text": text,
            })
            logger.info(f"Email sent via Resend to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via Resend to {to}: {e}")
            return False


class EmailService:
    """Email service with template rendering and provider abstraction."""

    def __init__(self):
        self._provider: Optional[EmailProvider] = None

    def _get_provider(self) -> Optional[EmailProvider]:
        """Lazy load the email provider based on settings."""
        if self._provider is None:
            settings = get_settings()
            if settings.email_provider == "smtp":
                self._provider = SMTPProvider()
            elif settings.email_provider == "resend":
                self._provider = ResendProvider()
            else:
                logger.warning(f"Unknown email provider: {settings.email_provider}")
        return self._provider

    def _build_link(self, path: str, token: str) -> str:
        """Build frontend URL with token parameter."""
        settings = get_settings()
        base_url = settings.frontend_url.rstrip("/")
        return f"{base_url}/{path}?token={token}"

    async def send_password_reset(self, email: str, token: str) -> bool:
        """Send password reset email."""
        settings = get_settings()
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send password reset to {email}")
            return False

        provider = self._get_provider()
        if not provider:
            logger.warning("No email provider configured")
            return False

        reset_link = self._build_link("reset-password", token)
        context = {
            "user_email": email,
            "reset_link": reset_link,
            "app_name": "OSFeed",
            "expire_time": f"{settings.password_reset_token_expire_minutes} minutes",
        }

        html = template_renderer.render("password_reset.html", **context)
        text = template_renderer.render("password_reset.txt", **context)

        return await provider.send(
            to=email,
            subject="Reset your OSFeed password",
            html=html,
            text=text,
        )

    async def send_verification(self, email: str, token: str) -> bool:
        """Send email verification email."""
        settings = get_settings()
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send verification to {email}")
            return False

        provider = self._get_provider()
        if not provider:
            logger.warning("No email provider configured")
            return False

        verify_link = self._build_link("verify-email", token)
        context = {
            "user_email": email,
            "verify_link": verify_link,
            "app_name": "OSFeed",
            "expire_time": f"{settings.email_verification_token_expire_hours} hours",
        }

        html = template_renderer.render("verification.html", **context)
        text = template_renderer.render("verification.txt", **context)

        return await provider.send(
            to=email,
            subject="Verify your OSFeed email",
            html=html,
            text=text,
        )


# Singleton
email_service = EmailService()
