"""Unit tests for export utility functions."""
import csv
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace

import pytest

from app.utils.export import (
    MESSAGE_CSV_COLUMNS,
    create_csv_writer,
    generate_csv_row,
    generate_html_template,
    generate_html_article,
    generate_pdf_bytes,
    WEASYPRINT_AVAILABLE,
)


class TestMessageCSVColumns:
    """Test MESSAGE_CSV_COLUMNS constant."""

    def test_csv_columns_defined(self) -> None:
        """Verify MESSAGE_CSV_COLUMNS contains expected columns."""
        assert MESSAGE_CSV_COLUMNS == [
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


class TestCreateCSVWriter:
    """Test create_csv_writer function."""

    def test_create_writer_with_default_buffer(self) -> None:
        """Create CSV writer with auto-generated buffer."""
        writer, output = create_csv_writer()

        assert hasattr(writer, "writerow")
        assert isinstance(output, StringIO)
        assert output.getvalue() == ""

    def test_create_writer_with_provided_buffer(self) -> None:
        """Create CSV writer with provided buffer."""
        existing_buffer = StringIO()
        writer, output = create_csv_writer(existing_buffer)

        assert hasattr(writer, "writerow")
        assert output is existing_buffer

    def test_writer_functionality(self) -> None:
        """Verify the writer can write rows."""
        writer, output = create_csv_writer()
        writer.writerow(["test", "data"])

        assert "test,data" in output.getvalue()


class TestGenerateCSVRow:
    """Test generate_csv_row function."""

    def test_generate_row_with_all_fields(self) -> None:
        """Generate CSV row with all fields populated."""
        message = SimpleNamespace(
            id="msg-123",
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="Hello World",
            translated_text="Bonjour le monde",
            source_language="en",
            target_language="fr",
            is_duplicate=False,
        )
        channel = SimpleNamespace(
            title="Test Channel",
            username="test_channel",
        )

        row = generate_csv_row(message, channel)

        assert row == [
            "msg-123",
            "Test Channel",
            "test_channel",
            datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "Hello World",
            "Bonjour le monde",
            "en",
            "fr",
            False,
        ]

    def test_generate_row_with_none_values(self) -> None:
        """Generate CSV row when optional fields are None."""
        message = SimpleNamespace(
            id="msg-456",
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text=None,
            translated_text=None,
            source_language=None,
            target_language=None,
            is_duplicate=True,
        )
        channel = SimpleNamespace(
            title="Empty Channel",
            username="empty",
        )

        row = generate_csv_row(message, channel)

        assert row[4] == ""  # original_text
        assert row[5] == ""  # translated_text
        assert row[6] == ""  # source_language
        assert row[7] == ""  # target_language
        assert row[8] is True  # is_duplicate

    def test_generate_row_with_special_characters(self) -> None:
        """Generate CSV row with special characters and unicode."""
        message = SimpleNamespace(
            id="msg-789",
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text='Text with "quotes" and commas, etc.',
            translated_text="Texte avec émojis 🎉 et accents éàü",
            source_language="en",
            target_language="fr",
            is_duplicate=False,
        )
        channel = SimpleNamespace(
            title="Special <>&",
            username="special_chars",
        )

        row = generate_csv_row(message, channel)

        assert row[1] == "Special <>&"
        assert row[4] == 'Text with "quotes" and commas, etc.'
        assert row[5] == "Texte avec émojis 🎉 et accents éàü"

    def test_generate_row_writes_to_csv(self) -> None:
        """Verify generated row can be written to CSV."""
        message = SimpleNamespace(
            id="msg-write",
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="Test",
            translated_text="Test FR",
            source_language="en",
            target_language="fr",
            is_duplicate=False,
        )
        channel = SimpleNamespace(
            title="Channel",
            username="channel",
        )

        writer, output = create_csv_writer()
        row = generate_csv_row(message, channel)
        writer.writerow(row)

        content = output.getvalue()
        assert "msg-write" in content
        assert "Channel" in content
        assert "Test" in content


class TestGenerateHTMLTemplate:
    """Test generate_html_template function."""

    def test_generate_template_with_default_title(self) -> None:
        """Generate HTML template with default title."""
        html = generate_html_template()

        assert "<!DOCTYPE html>" in html
        assert "<html lang='fr'>" in html
        assert "<title>OSFeed - Messages</title>" in html
        assert "<style>" in html
        assert "<body>" in html

    def test_generate_template_with_custom_title(self) -> None:
        """Generate HTML template with custom title."""
        html = generate_html_template("Custom Export Title")

        assert "<title>Custom Export Title</title>" in html

    def test_template_escapes_html_in_title(self) -> None:
        """Verify HTML special characters in title are escaped."""
        html = generate_html_template("Title with <script>alert('xss')</script>")

        assert "&lt;script&gt;" in html
        assert "<script>" not in html

    def test_template_includes_styles(self) -> None:
        """Verify template includes CSS styles."""
        html = generate_html_template()

        assert "font-family:Arial" in html
        assert "background:#f8fafc" in html
        assert "article{" in html

    def test_template_structure(self) -> None:
        """Verify template has proper HTML structure."""
        html = generate_html_template()

        assert html.startswith("<!DOCTYPE html>")
        assert html.endswith("<body>")
        assert "<meta charset='utf-8'>" in html


class TestGenerateHTMLArticle:
    """Test generate_html_article function."""

    def test_generate_article_with_translated_text(self) -> None:
        """Generate article with both original and translated text."""
        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="Hello World",
            translated_text="Bonjour le monde",
        )
        channel = SimpleNamespace(
            title="Test Channel",
            username="test_channel",
        )

        article = generate_html_article(message, channel)

        assert "<article>" in article
        assert "</article>" in article
        assert "Test Channel" in article
        assert "test_channel" in article
        assert "Bonjour le monde" in article
        assert "Original: Hello World" in article

    def test_generate_article_with_only_original_text(self) -> None:
        """Generate article with only original text (no translation)."""
        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="No translation needed",
            translated_text=None,
        )
        channel = SimpleNamespace(
            title="Channel",
            username="channel_user",
        )

        article = generate_html_article(message, channel)

        assert "No translation needed" in article
        assert "Original:" not in article

    def test_generate_article_with_only_translated_text(self) -> None:
        """Generate article with only translated text (no original)."""
        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text=None,
            translated_text="Only translation",
        )
        channel = SimpleNamespace(
            title="Channel",
            username="channel_user",
        )

        article = generate_html_article(message, channel)

        assert "Only translation" in article
        assert "Original:" not in article

    def test_generate_article_with_empty_text(self) -> None:
        """Generate article when both texts are None."""
        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text=None,
            translated_text=None,
        )
        channel = SimpleNamespace(
            title="Empty Channel",
            username="empty",
        )

        article = generate_html_article(message, channel)

        assert "<article>" in article
        assert "<p></p>" in article

    def test_article_escapes_html_content(self) -> None:
        """Verify HTML in content is properly escaped."""
        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="<script>alert('xss')</script>",
            translated_text="<b>Bold</b> & <i>Italic</i>",
        )
        channel = SimpleNamespace(
            title="<Channel>",
            username="<username>",
        )

        article = generate_html_article(message, channel)

        assert "&lt;Channel&gt;" in article
        assert "&lt;username&gt;" in article
        assert "&lt;b&gt;Bold&lt;/b&gt;" in article
        assert "&lt;script&gt;" in article
        assert "<script>" not in article

    def test_article_handles_special_characters(self) -> None:
        """Generate article with unicode and special characters."""
        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="Émojis 🎉 and unicode éàü",
            translated_text="Special chars: & < > \" '",
        )
        channel = SimpleNamespace(
            title="Spéciàl Çhännel",
            username="unicode_test",
        )

        article = generate_html_article(message, channel)

        assert "🎉" in article
        assert "Spéciàl Çhännel" in article
        assert "&amp;" in article
        assert "&lt;" in article
        assert "&gt;" in article


class TestGeneratePDFBytes:
    """Test generate_pdf_bytes function."""

    def test_generate_pdf_from_simple_html(self) -> None:
        """Generate PDF from simple HTML content."""
        if not WEASYPRINT_AVAILABLE:
            pytest.skip("weasyprint not installed")

        html_content = generate_html_template("Test PDF")
        html_content += "<h1>Test Content</h1></body></html>"

        pdf_bytes = generate_pdf_bytes(html_content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_pdf_from_complex_html(self) -> None:
        """Generate PDF from HTML with articles."""
        if not WEASYPRINT_AVAILABLE:
            pytest.skip("weasyprint not installed")

        message = SimpleNamespace(
            published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            original_text="Original",
            translated_text="Translated",
        )
        channel = SimpleNamespace(
            title="Channel",
            username="channel",
        )

        html_content = generate_html_template("Complex PDF")
        html_content += generate_html_article(message, channel)
        html_content += "</body></html>"

        pdf_bytes = generate_pdf_bytes(html_content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_pdf_raises_when_weasyprint_unavailable(self) -> None:
        """Verify proper error when weasyprint is not available."""
        import app.utils.export as export_module

        # Temporarily disable weasyprint
        original_available = export_module.WEASYPRINT_AVAILABLE
        export_module.WEASYPRINT_AVAILABLE = False

        try:
            with pytest.raises(RuntimeError) as exc_info:
                generate_pdf_bytes("<html><body>Test</body></html>")

            assert "weasyprint is not installed" in str(exc_info.value)
        finally:
            # Restore original state
            export_module.WEASYPRINT_AVAILABLE = original_available

    def test_generate_pdf_with_unicode_content(self) -> None:
        """Generate PDF with unicode characters."""
        if not WEASYPRINT_AVAILABLE:
            pytest.skip("weasyprint not installed")

        html_content = generate_html_template("Unicode Test")
        html_content += "<p>Émojis 🎉 éàü çñ</p></body></html>"

        pdf_bytes = generate_pdf_bytes(html_content)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")
