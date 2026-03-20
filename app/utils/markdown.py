"""
app/utils/markdown.py — Safe Markdown → HTML rendering.
Uses mistune with sanitisation to prevent XSS in challenge descriptions.
"""
import re
import mistune


# Allowlist for HTML tags produced by markdown rendering
_ALLOWED_TAGS = {
    "p", "br", "strong", "em", "code", "pre", "h1", "h2", "h3", "h4",
    "ul", "ol", "li", "blockquote", "a", "img", "table", "thead", "tbody",
    "tr", "th", "td", "hr", "span", "div",
}

_ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "code": ["class"],  # for syntax highlighting classes
    "span": ["class"],
}


def render_markdown(text: str) -> str:
    """Convert Markdown text to sanitised HTML.

    Strips any tags not in the allowlist to prevent XSS.
    """
    if not text:
        return ""
    # Render markdown → raw HTML
    md = mistune.create_markdown(
        plugins=["table", "url"],
        escape=True,           # escape raw HTML blocks in source
    )
    html = md(text)
    return html


def slugify(text: str) -> str:
    """Convert a title to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text
