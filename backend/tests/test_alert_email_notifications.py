import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.email_service import (
    EmailService,
    template_renderer,
)


# ---------------------------------------------------------------------------
# TemplateRenderer - Alert Templates
# ---------------------------------------------------------------------------


class TestAlertTemplateRenderer:
    def test_render_alert_triggered_html(self):
        context = {
            "user_email": "user@example.com",
            "alert_name": "High Volume Alert",
            "summary": "5 matching messages in the last 15 minutes.",
            "message_count": 5,
            "app_name": "OSFeed",
        }
        result = template_renderer.render("alert_triggered.html", **context)
        assert "user@example.com" in result or "High Volume Alert" in result
        assert "Error rendering" not in result
        assert "OSFeed" in result

    def test_render_alert_triggered_txt(self):
        context = {
            "user_email": "user@example.com",
            "alert_name": "Keyword Monitor",
            "summary": "10 matching messages in the last 60 minutes.",
            "message_count": 10,
            "app_name": "OSFeed",
        }
        result = template_renderer.render("alert_triggered.txt", **context)
        assert "Keyword Monitor" in result
        assert "10" in result or "matching messages" in result
        assert "Error rendering" not in result

    def test_render_alert_triggered_html_with_special_chars(self):
        context = {
            "user_email": "test@example.com",
            "alert_name": "Alert & <Test>",
            "summary": "2 messages with 'quotes' detected",
            "message_count": 2,
            "app_name": "OSFeed",
        }
        result = template_renderer.render("alert_triggered.html", **context)
        # Jinja2 autoescape should handle special characters
        assert "Error rendering" not in result
        assert "OSFeed" in result


# ---------------------------------------------------------------------------
# EmailService – send_alert_triggered when email disabled
# ---------------------------------------------------------------------------


class TestEmailServiceAlertDisabled:
    @pytest.mark.asyncio
    async def test_send_alert_triggered_returns_false_when_disabled(self):
        with patch("app.services.email_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(email_enabled=False)
            service = EmailService()
            result = await service.send_alert_triggered(
                "user@example.com",
                "Test Alert",
                "5 messages detected",
                5
            )
            assert result is False


# ---------------------------------------------------------------------------
# EmailService – send_alert_triggered with mocked provider
# ---------------------------------------------------------------------------


def _make_settings(**overrides):
    defaults = dict(
        email_enabled=True,
        email_provider="smtp",
        email_from_address="noreply@osfeed.test",
        email_from_name="OSFeed",
        frontend_url="http://localhost:5173",
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


class TestEmailServiceSendAlertTriggered:
    @pytest.mark.asyncio
    async def test_send_alert_triggered_calls_provider(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider
            result = await service.send_alert_triggered(
                "user@example.com",
                "Critical Alert",
                "15 messages in last hour",
                15
            )

        assert result is True
        mock_provider.send.assert_called_once()
        call_kwargs = mock_provider.send.call_args.kwargs
        assert call_kwargs["to"] == "user@example.com"
        assert call_kwargs["subject"] == "Alert Triggered: Critical Alert"
        assert "Critical Alert" in call_kwargs["html"]
        assert "15" in call_kwargs["text"] or "15 messages" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_alert_triggered_returns_false_on_provider_failure(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = False

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider
            result = await service.send_alert_triggered(
                "user@example.com",
                "Test Alert",
                "Summary text",
                1
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_triggered_returns_false_when_no_provider(self):
        with patch("app.services.email_service.get_settings", return_value=_make_settings(email_provider="unknown")):
            service = EmailService()
            result = await service.send_alert_triggered(
                "user@example.com",
                "Test Alert",
                "Summary",
                1
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_triggered_with_large_message_count(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider
            result = await service.send_alert_triggered(
                "user@example.com",
                "High Volume Alert",
                "1000 messages detected",
                1000
            )

        assert result is True
        call_kwargs = mock_provider.send.call_args.kwargs
        assert "1000" in call_kwargs["html"]

    @pytest.mark.asyncio
    async def test_send_alert_triggered_subject_includes_alert_name(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider

            await service.send_alert_triggered(
                "user@example.com",
                "Security Alert",
                "Security keywords detected",
                3
            )

        call_kwargs = mock_provider.send.call_args.kwargs
        assert call_kwargs["subject"] == "Alert Triggered: Security Alert"

    @pytest.mark.asyncio
    async def test_send_alert_triggered_renders_both_html_and_text(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider

            await service.send_alert_triggered(
                "user@example.com",
                "Test Alert",
                "Test summary",
                5
            )

        call_kwargs = mock_provider.send.call_args.kwargs
        # Verify both HTML and text content were provided
        assert call_kwargs["html"]
        assert call_kwargs["text"]
        # Verify they contain expected content
        assert "Test Alert" in call_kwargs["html"]
        assert "Test Alert" in call_kwargs["text"]
        assert "user@example.com" in call_kwargs["html"]
        assert "user@example.com" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_alert_triggered_includes_all_context_variables(self):
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider

            await service.send_alert_triggered(
                email="test@example.com",
                alert_name="Complete Alert",
                summary="20 messages in last 15 minutes",
                message_count=20
            )

        call_kwargs = mock_provider.send.call_args.kwargs
        html_content = call_kwargs["html"]
        text_content = call_kwargs["text"]

        # Verify all key context variables appear in rendered templates
        assert "Complete Alert" in html_content
        assert "20" in html_content or "20 messages" in html_content
        assert "OSFeed" in html_content

        assert "Complete Alert" in text_content
        assert "20" in text_content
        assert "test@example.com" in text_content


# ---------------------------------------------------------------------------
# EmailService method signature validation
# ---------------------------------------------------------------------------


class TestEmailServiceMethodSignature:
    def test_send_alert_triggered_method_exists(self):
        service = EmailService()
        assert hasattr(service, 'send_alert_triggered')
        assert callable(getattr(service, 'send_alert_triggered'))

    @pytest.mark.asyncio
    async def test_send_alert_triggered_accepts_correct_parameters(self):
        """Verify the method accepts the expected parameters."""
        mock_provider = AsyncMock()
        mock_provider.send.return_value = True

        with patch("app.services.email_service.get_settings", return_value=_make_settings()):
            service = EmailService()
            service._provider = mock_provider

            # Should not raise TypeError
            result = await service.send_alert_triggered(
                email="test@example.com",
                alert_name="Test",
                summary="Summary",
                message_count=1
            )

            assert isinstance(result, bool)
