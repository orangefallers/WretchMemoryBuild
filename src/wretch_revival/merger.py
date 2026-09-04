import re
from collections import defaultdict, deque
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .paths import BACKUP_ROOT, PROJECT_ROOT
from .utils import compact_date, safe_filename


MEDIA_PLACEHOLDER = re.compile(r"\{###_(.*?)_###\}")
MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


class _ImageScanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        if tag.lower() == "img":
            source = dict(attrs).get("src")
            if source:
                self.sources.append(source)

    def handle_startendtag(self, tag: str, attrs: List[tuple]) -> None:
        self.handle_starttag(tag, attrs)


def _basename(value: str) -> str:
    parsed = urlparse(value)
    return Path(parsed.path or value).name


def _find_local_media() -> Dict[str, Path]:
    result: Dict[str, Path] = {}
    for path in BACKUP_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS:
            result.setdefault(path.name, path)
    return result


def _relative_source(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _media_records(xml_html: str, mt_urls: List[str], local_media: Dict[str, Path]) -> List[Dict[str, Any]]:
    placeholders = MEDIA_PLACEHOLDER.findall(xml_html)
    scanner = _ImageScanner()
    scanner.feed(xml_html)
    direct_urls = scanner.sources
    urls_by_name = {_basename(url): url for url in mt_urls}
    records: List[Dict[str, Any]] = []
    seen: set = set()

    for reference in placeholders:
        filename = _basename(reference)
        url = urls_by_name.get(filename)
        key = (reference, url)
        if key in seen:
            continue
        seen.add(key)
        local = local_media.get(filename)
        records.append(
            {
                "original_ref": reference,
                "original_url": url,
                "filename": filename,
                "available": local is not None,
                "source_path": _relative_source(local),
                "output_name": safe_filename(filename),
            }
        )

    for url in direct_urls:
        filename = _basename(url)
        key = (url, url)
        if key in seen:
            continue
        seen.add(key)
        local = local_media.get(filename)
        records.append(
            {
                "original_ref": url,
                "original_url": url,
                "filename": filename,
                "available": local is not None,
                "source_path": _relative_source(local),
                "output_name": safe_filename(filename),
            }
        )
    return records


def merge_sources(xml: Dict[str, Any], mt: Dict[str, Any]) -> Dict[str, Any]:
    mt_by_key: Dict[Tuple[str, str], Deque[Dict[str, Any]]] = defaultdict(deque)
    for record in mt["posts"]:
        mt_by_key[(record["title"], record["date"])].append(record)

    local_media = _find_local_media()
    warnings: List[str] = []
    merged_posts: List[Dict[str, Any]] = []

    for position, source_post in enumerate(xml["posts"]):
        post = dict(source_post)
        key = (post["title"], post["date"])
        mt_post = mt_by_key[key].popleft() if mt_by_key[key] else None
        if mt_post is None and position < len(mt["posts"]):
            candidate = mt["posts"][position]
            if candidate["title"] == post["title"]:
                mt_post = candidate
                warnings.append(f"POST {post['id']}: 以來源順序配對 Movable Type")
        if mt_post is None:
            warnings.append(f"POST {post['id']}: 找不到對應的 Movable Type 文章")

        post["slug"] = f"{compact_date(post['date'])}-{post['id']}"
        post["tags"] = mt_post["tags"] if mt_post else []
        post["mt_status"] = mt_post["status"] if mt_post else None
        post["media"] = _media_records(
            post["content_html"], mt_post["image_urls"] if mt_post else [], local_media
        )
        post["original_url"] = (
            f"http://www.wretch.cc/blog/{xml['profile']['blog_id']}/{post['id']}"
        )
        expected_status = "publish" if post["visibility"] == "public" else "draft"
        if mt_post and mt_post["status"] != expected_status:
            warnings.append(
                f"POST {post['id']}: XML visibility={post['visibility']}，"
                f"MT status={mt_post['status']}"
            )
        merged_posts.append(post)

    post_map = {post["id"]: post for post in merged_posts}
    for post in merged_posts:
        post["comment_ids"] = []
    for comment in xml["comments"]:
        if comment["post_id"] in post_map:
            post_map[comment["post_id"]]["comment_ids"].append(comment["id"])

    unmatched_mt = sum(len(queue) for queue in mt_by_key.values())
    if unmatched_mt:
        warnings.append(f"有 {unmatched_mt} 篇 Movable Type 文章未配對")

    return {
        "profile": xml["profile"],
        "posts": merged_posts,
        "comments": xml["comments"],
        "sources": {"xml": xml["source"], "movable_type": mt["source"]},
        "warnings": warnings,
    }

