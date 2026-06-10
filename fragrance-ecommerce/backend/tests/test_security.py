"""Security hardening — sanitization, password strength, headers."""
import pytest
from pydantic import ValidationError

from app.core.sanitize import strip_html, sanitize_str
from app.schemas.customer import RegisterRequest, ResetPasswordRequest


# ---------------------------------------------------------------------------
# HTML sanitization
# ---------------------------------------------------------------------------

def test_strip_script_tags():
    assert strip_html('<script>alert("xss")</script>hello') == "hello"


def test_strip_inline_event_handlers():
    result = strip_html('<p onclick="evil()">text</p>')
    assert "onclick" not in result
    assert "text" in result


def test_strip_javascript_href():
    result = strip_html('<a href="javascript:void(0)">click</a>')
    assert "javascript:" not in result


def test_allowed_tags_preserved():
    result = strip_html("<p>Hello <strong>world</strong></p>")
    assert "<p>" in result
    assert "<strong>" in result
    assert "Hello" in result


def test_strip_style_blocks():
    result = strip_html("<style>body{color:red}</style>content")
    assert "<style>" not in result
    assert "content" in result


def test_none_passthrough():
    assert strip_html(None) is None
    assert sanitize_str(None) is None


def test_max_length_truncation():
    assert len(sanitize_str("a" * 200, max_length=10)) == 10  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Password strength (RegisterRequest)
# ---------------------------------------------------------------------------

def test_register_strong_password_accepted():
    req = RegisterRequest(email="a@b.com", password="Secure1Pass")
    assert req.password == "Secure1Pass"


def test_register_password_too_short():
    with pytest.raises(ValidationError, match="at least 8"):
        RegisterRequest(email="a@b.com", password="Ab1")


def test_register_password_no_uppercase():
    with pytest.raises(ValidationError, match="uppercase"):
        RegisterRequest(email="a@b.com", password="lowercase1")


def test_register_password_no_lowercase():
    with pytest.raises(ValidationError, match="lowercase"):
        RegisterRequest(email="a@b.com", password="ALLCAPS1")


def test_register_password_no_digit():
    with pytest.raises(ValidationError, match="digit"):
        RegisterRequest(email="a@b.com", password="NoDigitHere")


def test_reset_password_same_rules():
    with pytest.raises(ValidationError, match="digit"):
        ResetPasswordRequest(token="tok", new_password="NoDigitHere")


# ---------------------------------------------------------------------------
# Security headers middleware (unit-level smoke test)
# ---------------------------------------------------------------------------

def test_security_headers_constants():
    from app.middleware.security import _COMMON_HEADERS
    assert "X-Content-Type-Options" in _COMMON_HEADERS
    assert "X-Frame-Options" in _COMMON_HEADERS
    assert "Content-Security-Policy" in _COMMON_HEADERS
    assert _COMMON_HEADERS["X-Frame-Options"] == "DENY"
    assert _COMMON_HEADERS["X-Content-Type-Options"] == "nosniff"


def test_csp_blocks_unsafe_sources():
    from app.middleware.security import _COMMON_HEADERS
    csp = _COMMON_HEADERS["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    # Stripe iframes must be allowed
    assert "https://js.stripe.com" in csp
