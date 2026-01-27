import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.email_service import (
    EmailService,
    SMTPProvider,
    ResendProvider,
    TemplateRenderer,
    template_renderer,
)


# ---------------------------------------------------------------------------
# TemplateRenderer
# ---------------------------------------------------------------------------


class TestTemplateRenderer:
    def test_render_verification_html(self):
        context = {
            "user_email": "u@example.com",
            "verify_link": "http://localhost/verify-email?token=abc",
            "app_name": "OSFeed",
            "expire_time": "24 hours",
        }
        result = template_renderer.render("verification.html", **context)
        assert "u@example.com" in result or "verify-email?token=abc" in result
        assert "Error rendering" not in result

    def test_render_password_reset_txt(self):
        context = {
            "user_email": "u@example.com",
            "reset_link": "http://localhost/reset-password?token=xyz",
            "app_name": "OSFeed",
            "expire_time": "30 minutes",
        }
        result = template_renderer.render("password_reset.txt", **context)
        assert "reset-password?token=xyz" in result
        assert "Error rendering" not in result

    def test_render_missing_template_returns_fallback(self):
        result = template_renderer.render("nonexistent.html")
        assert "Error rendering" in result


# ---------------------------------------------------------------------------
# EmailService – graceful degradation when email disabled
# ---------------------------------------------------------------------------


class TestEmailServiceDisabled:
    @pytest.mark.asyncio
    async def test_send_verification_returns_false_when_disabled(self):
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(email_enabled=False)
            service = EmailService()
            result = await service.send_verification("u@example.com", "tok")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_password_reset_returns_false_when_disabled(self):
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(email_enabled=False)
            service = EmailService()
            result = await service.send_password_reset("u@example.com", "tok")
            assert result is False


# ---------------------------------------------------------------------------
# EmailService – with mocked provider
# ---------------------------------------------------------------------------


def _make_settings(**overrides):
    defaults = dict(
        email_enabled=True,
        email_provider="smtp",
        email_from_address="noreply@osfeed.test",
        email_from_name="OSFeed",
        frontend_url="http://localhost:5173",
        password_reset_token_expire_minutes=30,
        email_verification_token_expire_hours=24,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


class TestEmailServiceWithMockedProvider:
    @pytest.mark.asyncio
    async def test_send_verification_calls_provider(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider
            result = await service.send_verification("u@example.com", "verify-tok")

        assert result is True
        mock_provider.send.assert_called_once()
        call_kwargs = mock_provider.send.call_args.kwargs
        assert call_kwargs["to"] == "u@example.com"
        assert call_kwargs["subject"] == "Verify your OSFeed email"

    @pytest.mark.asyncio
    async def test_send_password_reset_calls_provider(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider
            result = await service.send_password_reset("u@example.com", "reset-tok")

        assert result is True
        mock_provider.send.assert_called_once()
        call_kwargs = mock_provider.send.call_args.kwargs
        assert call_kwargs["to"] == "u@example.com"
        assert call_kwargs["subject"] == "Reset your OSFeed password"

    @pytest.mark.asyncio
    async def test_send_verification_returns_false_on_provider_failure(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = False

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider
            result = await service.send_verification("u@example.com", "tok")

        assert result is False

    @pytest.mark.asyncio
    async def test_build_link_includes_token(self):
        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            link = service._build_link("verify-email", "abc123")
            assert link == "http://localhost:5173/verify-email?token=abc123"


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------


class TestProviderSelection:
    def test_smtp_provider_selected(self):
        with patch("app.services.email_service.get_settings", return_value=_make_settings(email_provider="smtp")):
            service = EmailService()
            provider = service._get_provider()
            assert isinstance(provider, SMTPProvider)

    def test_resend_provider_selected(self):
        with patch("app.services.email_service.get_settings", return_value=_make_settings(email_provider="resend")):
            service = EmailService()
            provider = service._get_provider()
            assert isinstance(provider, ResendProvider)

    def test_unknown_provider_returns_none(self):
        with patch("app.services.email_service.get_settings", return_value=_make_settings(email_provider="unknown")):
            service = EmailService()
            provider = service._get_provider()
            assert provider is None
