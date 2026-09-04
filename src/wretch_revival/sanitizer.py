import html
import re
from pathlib import Path
from typing import Any, Dict, Iterable
from urllib.parse import urlparse

import bleach


DANGEROUS_BLOCKS = re.compile(
    r"<(script|iframe|object|embed|applet)\b[^>]*>.*?</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
DANGEROUS_SINGLE = re.compile(
    r"<(script|iframe|object|embed|applet)\b[^>]*?/?>",
    re.IGNORECASE | re.DOTALL,
)
MEDIA_PLACEHOLDER = re.compile(r"\{###_(.*?)_###\}")
IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_ATTRIBUTE = re.compile(
    r"\bsrc\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
    re.IGNORECASE,
)

ALLOWED_TAGS = {
    "a",
    "b",
    "blockquote",
    "br",
    "center",
    "div",
    "em",
    "font",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "small",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
}
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "div": ["class", "data-original-media"],
    "font": ["color", "face", "size"],
    "img": ["src", "alt", "title", "width", "height"],
    "span": ["class"],
    "table": ["border", "cellpadding", "cellspacing", "width"],
    "td": ["colspan", "rowspan", "width"],
    "th": ["colspan", "rowspan", "width"],
}


def _basename(value: str) -> str:
    parsed = urlparse(value)
    return Path(parsed.path or value).name


def _media_map(media: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in media:
        for key in (item.get("original_ref"), item.get("original_url"), item.get("filename")):
            if key:
                result[key] = item
                result[_basename(key)] = item
    return result


def _missing_media(reference: str) -> str:
    label = html.escape(_basename(reference) or reference)
    original = html.escape(_basename(reference) or "unknown-image", quote=True)
    return (
        f'<div class="missing-image" data-original-media="{original}">'
        f'<span aria-hidden="true">▧</span> 歷史圖片已遺失'
        f'<small>{label}</small></div>'
    )


def sanitize_html(
    content: str,
    media: Iterable[Dict[str, Any]] = (),
    image_prefix: str = "images/",
) -> str:
    media_by_ref = _media_map(media)
    content = DANGEROUS_BLOCKS.sub("", content or "")
    content = DANGEROUS_SINGLE.sub("", content)

    def placeholder(match: re.Match) -> str:
        reference = match.group(1)
        item = media_by_ref.get(reference) or media_by_ref.get(_basename(reference))
        if item and item.get("available"):
            src = html.escape(image_prefix + item["output_name"], quote=True)
            return f'<img src="{src}" alt="">'
        return _missing_media(reference)

    content = MEDIA_PLACEHOLDER.sub(placeholder, content)

    def image_tag(match: re.Match) -> str:
        tag = match.group(0)
        src_match = SRC_ATTRIBUTE.search(tag)
        if not src_match:
            return _missing_media("unknown-image")
        source = next(value for value in src_match.groups() if value is not None)
        item = media_by_ref.get(source) or media_by_ref.get(_basename(source))
        if item and item.get("available"):
            src = html.escape(image_prefix + item["output_name"], quote=True)
            return f'<img src="{src}" alt="">'
        return _missing_media(source)

    content = IMG_TAG.sub(image_tag, content)
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        strip=True,
        strip_comments=True,
    )
