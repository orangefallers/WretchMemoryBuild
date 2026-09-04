import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

from .models import comment_visibility, optional_text, post_visibility
from .utils import sha256_file, to_iso


def _text(node: ET.Element, field: str) -> str:
    return (node.findtext(field) or "").strip()


def parse_xml(path: Path) -> Dict[str, Any]:
    root = ET.parse(path).getroot()
    if root.tag != "blog_backup":
        raise ValueError(f"不支援的 XML 根節點：{root.tag}")

    blog = root.find("./blog_blogs")
    if blog is None:
        raise ValueError("XML 缺少 blog_blogs")

    profile = {
        "blog_id": _text(blog, "id"),
        "nickname": _text(blog, "nickname"),
        "blog_title": _text(blog, "name"),
        "description": _text(blog, "desc"),
        "declared_post_count": int(_text(blog, "NumPosts") or 0),
        "declared_comment_count": int(_text(blog, "NumComments") or 0),
        "last_published_at": to_iso(optional_text(_text(blog, "LastPubTime"))),
        "last_updated_at": to_iso(optional_text(_text(blog, "LastUpdate"))),
    }

    posts: List[Dict[str, Any]] = []
    for node in root.findall("./blog_articles/article"):
        post_id = _text(node, "id")
        if not post_id:
            raise ValueError("文章缺少 ID")
        posts.append(
            {
                "id": post_id,
                "title": _text(node, "title"),
                "content_html": _text(node, "text"),
                "date": to_iso(_text(node, "date")),
                "post_time": to_iso(_text(node, "PostTime")),
                "visibility": post_visibility(_text(node, "isCloak")),
                "source_visibility_code": _text(node, "isCloak"),
                "category_id": optional_text(_text(node, "category_id")),
                "class_id": optional_text(_text(node, "class_id")),
                "historical_counter": int(_text(node, "counter_week") or 0),
            }
        )

    comments: List[Dict[str, Any]] = []
    for node in root.findall("./blog_articles_comments/article_comment"):
        comments.append(
            {
                "id": _text(node, "id"),
                "post_id": _text(node, "article_id"),
                "author": optional_text(_text(node, "name")),
                "content_html": _text(node, "text"),
                "date": to_iso(_text(node, "date")),
                "visibility": comment_visibility(_text(node, "isCloak")),
                "source_visibility_code": _text(node, "isCloak"),
                "owner_reply_html": optional_text(_text(node, "reply")),
                "owner_reply_date": to_iso(optional_text(_text(node, "reply_date"))),
            }
        )

    return {
        "source": {
            "path": str(path),
            "sha256": sha256_file(path),
            "backup_version": (root.findtext("./backup_version") or "").strip(),
        },
        "profile": profile,
        "posts": posts,
        "comments": comments,
    }

