#!/usr/bin/env python3
"""Manual verification of export utility functions (no pytest required)."""
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

sys.path.insert(0, '.')

from app.utils.export import (
    MESSAGE_CSV_COLUMNS,
    create_csv_writer,
    generate_csv_row,
    generate_html_template,
    generate_html_article,
    generate_pdf_bytes,
    WEASYPRINT_AVAILABLE,
)


def test_message_csv_columns():
    """Test MESSAGE_CSV_COLUMNS constant."""
    expected = [
        "message_id", "channel_title", "channel_username", "published_at",
        "original_text", "translated_text", "source_language",
        "target_language", "is_duplicate"
    ]
    assert MESSAGE_CSV_COLUMNS == expected, "CSV columns mismatch"
    print("✓ MESSAGE_CSV_COLUMNS test passed")


def test_create_csv_writer():
    """Test create_csv_writer function."""
    writer, output = create_csv_writer()
    assert output.getvalue() == "", "Buffer should be empty"

    writer.writerow(["test", "data"])
    assert "test,data" in output.getvalue(), "Write failed"
    print("✓ create_csv_writer test passed")


def test_generate_csv_row():
    """Test generate_csv_row function."""
    message = SimpleNamespace(
        id="msg-123",
        published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        original_text="Hello World",
        translated_text="Bonjour",
        source_language="en",
        target_language="fr",
        is_duplicate=False,
    )
    channel = SimpleNamespace(title="Test", username="test_ch")

    row = generate_csv_row(message, channel)
    assert row[0] == "msg-123", "ID mismatch"
    assert row[1] == "Test", "Title mismatch"
    assert row[4] == "Hello World", "Text mismatch"

    # Test with None values
    message.original_text = None
    row2 = generate_csv_row(message, channel)
    assert row2[4] == "", "Should convert None to empty string"

    print("✓ generate_csv_row test passed")


def test_generate_html_template():
    """Test generate_html_template function."""
    html = generate_html_template()
    assert "<!DOCTYPE html>" in html, "Missing DOCTYPE"
    assert "<title>OSFeed - Messages</title>" in html, "Missing default title"
    assert "<style>" in html, "Missing styles"

    # Test custom title
    html2 = generate_html_template("Custom")
    assert "<title>Custom</title>" in html2, "Custom title failed"

    # Test HTML escaping
    html3 = generate_html_template("<script>alert('xss')</script>")
    assert "&lt;script&gt;" in html3, "HTML not escaped"
    assert "<script>" not in html3, "XSS vulnerability"

    print("✓ generate_html_template test passed")


def test_generate_html_article():
    """Test generate_html_article function."""
    message = SimpleNamespace(
        published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        original_text="Hello",
        translated_text="Bonjour",
    )
    channel = SimpleNamespace(title="Channel", username="ch")

    article = generate_html_article(message, channel)
    assert "<article>" in article, "Missing article tag"
    assert "Bonjour" in article, "Missing translated text"
    assert "Original: Hello" in article, "Missing original text"

    # Test HTML escaping
    message2 = SimpleNamespace(
        published_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        original_text="<script>",
        translated_text=None,
    )
    channel2 = SimpleNamespace(title="<Test>", username="test")
    article2 = generate_html_article(message2, channel2)
    assert "&lt;script&gt;" in article2, "HTML not escaped in article"
    assert "&lt;Test&gt;" in article2, "Channel title not escaped"

    print("✓ generate_html_article test passed")


def test_generate_pdf_bytes():
    """Test generate_pdf_bytes function."""
    if not WEASYPRINT_AVAILABLE:
        print("⚠ generate_pdf_bytes test skipped (weasyprint not installed)")
        # Still test error handling
        import app.utils.export as export_module
        original = export_module.WEASYPRINT_AVAILABLE
        export_module.WEASYPRINT_AVAILABLE = False
        try:
            generate_pdf_bytes("<html><body>Test</body></html>")
            assert False, "Should raise RuntimeError"
        except RuntimeError as e:
            assert "weasyprint is not installed" in str(e)
        finally:
            export_module.WEASYPRINT_AVAILABLE = original
        print("✓ generate_pdf_bytes error handling test passed")
    else:
        html = generate_html_template("PDF Test")
        html += "<h1>Test</h1></body></html>"
        pdf_bytes = generate_pdf_bytes(html)
        assert isinstance(pdf_bytes, bytes), "Should return bytes"
        assert len(pdf_bytes) > 0, "PDF should not be empty"
        assert pdf_bytes.startswith(b"%PDF"), "Should be valid PDF"
        print("✓ generate_pdf_bytes test passed")


def main():
    """Run all manual tests."""
    print("Running manual verification tests...\n")

    try:
        test_message_csv_columns()
        test_create_csv_writer()
        test_generate_csv_row()
        test_generate_html_template()
        test_generate_html_article()
        test_generate_pdf_bytes()

        print("\n" + "="*50)
        print("✓ All manual verification tests passed!")
        print("="*50)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
