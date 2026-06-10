"""Input sanitization helpers.

Strips dangerous HTML from any free-text field that might be displayed
back to users (product descriptions, customer notes, review text).
We deliberately keep this lightweight — no third-party deps — because
all API responses are JSON and the frontend is responsible for escaping
on render. This is a defence-in-depth layer.
"""
from __future__ import annotations
import re

# Tags that are harmless in stored content and may appear in rich descriptions.
_ALLOWED_TAGS = {"b", "i", "em", "strong", "p", "br", "ul", "ol", "li", "span"}

_TAG_RE = re.compile(r"<(/?)(\w+)([^>]*)>", re.IGNORECASE)
_SCRIPT_RE = re.compile(r"<script[\s\S]*?</script>", re.IGNORECASE)
_STYLE_RE = re.compile(r"<style[\s\S]*?</style>", re.IGNORECASE)
_EVENT_ATTR_RE = re.compile(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", re.IGNORECASE)
_JAVASCRIPT_HREF_RE = re.compile(r'href\s*=\s*["\']?\s*javascript:', re.IGNORECASE)


def strip_html(text: str | None) -> str | None:
    """Remove dangerous HTML while preserving allowed structural tags."""
    if text is None:
        return None
    text = _SCRIPT_RE.sub("", text)
    text = _STYLE_RE.sub("", text)
    text = _EVENT_ATTR_RE.sub("", text)
    text = _JAVASCRIPT_HREF_RE.sub('href="#"', text)

    def _replace_tag(m: re.Match) -> str:
        tag = m.group(2).lower()
        if tag in _ALLOWED_TAGS:
            attrs = m.group(3)
            attrs = _EVENT_ATTR_RE.sub("", attrs)
            return f"<{m.group(1)}{tag}{attrs}>"
        return ""

    return _TAG_RE.sub(_replace_tag, text).strip()


def sanitize_str(value: str | None, max_length: int | None = None) -> str | None:
    """Strip dangerous HTML and optionally truncate."""
    cleaned = strip_html(value)
    if cleaned and max_length:
        cleaned = cleaned[:max_length]
    return cleaned
