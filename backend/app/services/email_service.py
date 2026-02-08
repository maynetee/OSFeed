"""Email service with template rendering and provider abstraction."""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import aiosmtplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2.exceptions import TemplateError
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def _redact_email(email: str) -> str:
    """Redact email address for safe logging (e.g., u***@example.com)."""
    try:
        local, domain = email.split("@")
        return f"{local[0]}***@{domain}" if local else f"***@{domain}"
    except (ValueError, IndexError):
        return "***"


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
        except TemplateError as e:
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
        redacted = _redact_email(to)
        logger.info(f"SMTP: attempting to send email to {redacted}, subject='{subject}'")
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
            logger.info(f"SMTP: email sent successfully to {redacted}")
            return True
        except aiosmtplib.SMTPConnectError as e:
            logger.error(
                f"SMTP connection failed for {redacted}: host={settings.smtp_host}, "
                f"port={settings.smtp_port}, error={e}"
            )
            return False
        except aiosmtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed for {redacted}: {e}")
            return False
        except aiosmtplib.SMTPResponseException as e:
            logger.error(
                f"SMTP error for {redacted}: code={e.code}, message={e.message}"
            )
            return False
        except (smtplib.SMTPException, OSError) as e:
            logger.error(
                f"SMTP: unexpected error sending to {redacted}: {type(e).__name__}: {e}"
            )
            return False


class ResendProvider(EmailProvider):
    """Resend API email provider."""

    async def send(self, to: str, subject: str, html: str, text: str) -> bool:
        """Send email via Resend API."""
        settings = get_settings()
        redacted = _redact_email(to)
        logger.info(f"Resend: attempting to send email to {redacted}, subject='{subject}'")
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
            logger.info(f"Resend: email sent successfully to {redacted}")
            return True
        except ImportError:
            logger.error("Resend package not installed - cannot send email")
            return False
        except (httpx.HTTPError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(
                f"Resend: failed to send email to {redacted}: {type(e).__name__}: {e}"
            )
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
            logger.info(f"Email disabled - would send password reset to {_redact_email(email)}")
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
            logger.info(f"Email disabled - would send verification to {_redact_email(email)}")
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

    async def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email after signup."""
        settings = get_settings()
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send welcome to {_redact_email(email)}")
            return False

        provider = self._get_provider()
        if not provider:
            logger.warning("No email provider configured")
            return False

        context = {
            "username": username,
            "dashboard_link": f"{settings.frontend_url.rstrip('/')}/dashboard",
            "app_name": "OSFeed",
        }

        html = template_renderer.render("welcome.html", **context)
        text = template_renderer.render("welcome.txt", **context)

        return await provider.send(
            to=email,
            subject="Welcome to OSFeed!",
            html=html,
            text=text,
        )

    async def send_contact_confirmation(self, email: str, name: str) -> bool:
        """Send confirmation after contact form submission."""
        settings = get_settings()
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send contact confirmation to {_redact_email(email)}")
            return False

        provider = self._get_provider()
        if not provider:
            logger.warning("No email provider configured")
            return False

        context = {
            "name": name,
            "app_name": "OSFeed",
        }

        html = template_renderer.render("contact_confirmation.html", **context)
        text = template_renderer.render("contact_confirmation.txt", **context)

        return await provider.send(
            to=email,
            subject="We received your message - OSFeed",
            html=html,
            text=text,
        )

    async def send_newsletter_welcome(self, email: str) -> bool:
        """Send welcome email for newsletter subscription."""
        settings = get_settings()
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send newsletter welcome to {_redact_email(email)}")
            return False

        provider = self._get_provider()
        if not provider:
            logger.warning("No email provider configured")
            return False

        unsubscribe_link = f"{settings.frontend_url.rstrip('/')}/newsletter/unsubscribe?email={email}"
        context = {
            "unsubscribe_link": unsubscribe_link,
            "app_name": "OSFeed",
        }

        html = template_renderer.render("newsletter_welcome.html", **context)
        text = template_renderer.render("newsletter_welcome.txt", **context)

        return await provider.send(
            to=email,
            subject="Welcome to the OSFeed Newsletter!",
            html=html,
            text=text,
        )

    async def send_alert_triggered(
        self,
        email: str,
        alert_name: str,
        summary: str,
        message_count: int,
        keywords: list[str] | None = None,
        message_preview: str | None = None,
        alert_id: str | None = None,
    ) -> bool:
        """Send alert triggered notification email."""
        settings = get_settings()
        if not settings.email_enabled:
            logger.info(f"Email disabled - would send alert notification to {_redact_email(email)}")
            return False

        provider = self._get_provider()
        if not provider:
            logger.warning("No email provider configured")
            return False

        # Build links for the email
        base_url = settings.frontend_url.rstrip("/")
        alert_link = f"{base_url}/alerts/{alert_id}" if alert_id else f"{base_url}/alerts"
        unsubscribe_link = f"{base_url}/settings/notifications"

        context = {
            "user_email": email,
            "alert_name": alert_name,
            "summary": summary,
            "message_count": message_count,
            "keywords": keywords or [],
            "message_preview": message_preview or "",
            "alert_link": alert_link,
            "unsubscribe_link": unsubscribe_link,
            "app_name": "OSFeed",
        }

        html = template_renderer.render("alert_triggered.html", **context)
        text = template_renderer.render("alert_triggered.txt", **context)

        return await provider.send(
            to=email,
            subject=f"Alert Triggered: {alert_name}",
            html=html,
            text=text,
        )


# Singleton
email_service = EmailService()
