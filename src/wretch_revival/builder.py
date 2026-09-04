import html
import json
import math
import os
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .integrity import build_report
from .models import is_publishable
from .paths import (
    CONFIG_ROOT,
    DATA_ROOT,
    DIST_ROOT,
    PROJECT_ROOT,
    REPORTS_ROOT,
    STATIC_ROOT,
    TEMPLATES_ROOT,
)
from .sanitizer import sanitize_html
from .utils import read_json, write_json


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value or "")
    return " ".join("".join(parser.parts).split())


def _excerpt(value: str, length: int = 180) -> str:
    text = _plain_text(value)
    return text if len(text) <= length else text[:length].rstrip() + "……"


def _format_date(value: Optional[str]) -> str:
    if not value:
        return "日期不詳"
    dt = datetime.fromisoformat(value)
    return f"{dt.year}年{dt.month}月{dt.day}日 {dt:%H:%M}"


def _format_short_date(value: Optional[str]) -> str:
    if not value:
        return "日期不詳"
    dt = datetime.fromisoformat(value)
    return f"{dt.year}/{dt.month:02d}/{dt.day:02d}"


def _load_config(environment: str) -> Dict[str, Any]:
    supported = {"local", "production"}
    if environment not in supported:
        raise ValueError(f"不支援的環境：{environment}")
    config = json.loads((CONFIG_ROOT / "site.json").read_text(encoding="utf-8"))
    override_path = CONFIG_ROOT / "environments" / f"{environment}.json"
    config.update(json.loads(override_path.read_text(encoding="utf-8")))
    return config


def _root_path(output_path: Path, output_root: Path) -> str:
    relative = os.path.relpath(output_root, output_path.parent).replace(os.sep, "/")
    return "" if relative == "." else relative.rstrip("/") + "/"


def _archive_rows(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts = Counter(post["date"][:7] for post in posts if post.get("date"))
    rows = []
    for key, count in sorted(counts.items(), reverse=True):
        year, month = key.split("-")
        rows.append(
            {
                "key": key,
                "year": year,
                "month": month,
                "label": f"{int(year)}年{int(month)}月",
                "count": count,
                "path": f"archive/{year}/{month}.html",
            }
        )
    return rows


def _prepare_list_post(post: Dict[str, Any], comment_counts: Counter) -> Dict[str, Any]:
    result = dict(post)
    result["excerpt"] = _excerpt(post["content_html"])
    result["comment_count"] = comment_counts[post["id"]]
    return result


def build_site(
    data: Optional[Dict[str, Any]] = None,
    environment: str = "local",
) -> Dict[str, Any]:
    if data is None:
        data = {
            "profile": read_json(DATA_ROOT / "profile.json"),
            "posts": read_json(DATA_ROOT / "posts.json"),
            "comments": read_json(DATA_ROOT / "comments.json"),
        }
    config = _load_config(environment)
    output_root = DIST_ROOT / environment
    posts = data["posts"]
    comments = data["comments"]
    profile = dict(data["profile"])
    if config.get("site_name"):
        profile["blog_title"] = config["site_name"]
    if config.get("site_description"):
        profile["description"] = config["site_description"]

    generated_posts = [
        post for post in posts if is_publishable(post["visibility"], config["include_drafts"])
    ]
    generated_posts.sort(key=lambda post: (post.get("date") or "", post["id"]), reverse=True)
    generated_post_ids = {post["id"] for post in generated_posts}
    generated_comments = [
        comment
        for comment in comments
        if comment["post_id"] in generated_post_ids
        and (comment["visibility"] == "public" or config["include_hidden_comments"])
    ]
    comments_by_post: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for comment in generated_comments:
        comments_by_post[comment["post_id"]].append(comment)
    for values in comments_by_post.values():
        values.sort(key=lambda comment: comment.get("date") or "")
    comment_counts = Counter(comment["post_id"] for comment in generated_comments)

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)
    shutil.copytree(STATIC_ROOT, output_root, dirs_exist_ok=True)
    (output_root / ".nojekyll").write_text("", encoding="utf-8")

    copied_media = set()
    for post in generated_posts:
        for item in post.get("media", []):
            if not item.get("available") or not item.get("source_path"):
                continue
            source = PROJECT_ROOT / item["source_path"]
            destination = output_root / "images" / item["output_name"]
            if item["output_name"] not in copied_media:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied_media.add(item["output_name"])

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_ROOT),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["date_zh"] = _format_date
    env.filters["short_date"] = _format_short_date

    archives = _archive_rows(generated_posts)
    recent_posts = generated_posts[:10]

    def render(template_name: str, output: Path, **context: Any) -> None:
        root_path = _root_path(output, output_root)
        full_context = {
            "profile": profile,
            "config": config,
            "root_path": root_path,
            "recent_posts": recent_posts,
            "archives": archives,
            **context,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            env.get_template(template_name).render(**full_context),
            encoding="utf-8",
        )

    per_page = max(1, int(config.get("posts_per_page", 10)))
    page_count = max(1, math.ceil(len(generated_posts) / per_page))
    for page_number in range(1, page_count + 1):
        page_posts = generated_posts[(page_number - 1) * per_page : page_number * per_page]
        page_posts = [_prepare_list_post(post, comment_counts) for post in page_posts]
        output = output_root / "index.html" if page_number == 1 else output_root / "page" / str(page_number) / "index.html"
        render(
            "pages/index.html",
            output,
            page_title=profile["blog_title"],
            posts=page_posts,
            pagination={"current": page_number, "total": page_count},
        )

    chronological = sorted(generated_posts, key=lambda post: (post.get("date") or "", post["id"]))
    for index, post in enumerate(chronological):
        output = output_root / "blog" / f"{post['slug']}.html"
        root_path = _root_path(output, output_root)
        rendered_post = dict(post)
        rendered_post["rendered_html"] = sanitize_html(
            post["content_html"], post.get("media", []), root_path + "images/"
        )
        rendered_comments = []
        for comment in comments_by_post.get(post["id"], []):
            value = dict(comment)
            value["rendered_html"] = sanitize_html(comment["content_html"])
            value["rendered_reply_html"] = (
                sanitize_html(comment["owner_reply_html"])
                if comment.get("owner_reply_html")
                else None
            )
            rendered_comments.append(value)
        render(
            "pages/post.html",
            output,
            page_title=f"{post['title']} - {profile['blog_title']}",
            post=rendered_post,
            comments=rendered_comments,
            previous_post=chronological[index - 1] if index > 0 else None,
            next_post=chronological[index + 1] if index + 1 < len(chronological) else None,
        )

    render(
        "pages/archive-index.html",
        output_root / "archive" / "index.html",
        page_title=f"月份文章 - {profile['blog_title']}",
    )
    for archive in archives:
        month_posts = [post for post in generated_posts if post["date"].startswith(archive["key"])]
        month_posts = [_prepare_list_post(post, comment_counts) for post in month_posts]
        render(
            "pages/archive.html",
            output_root / "archive" / archive["year"] / f"{archive['month']}.html",
            page_title=f"{archive['label']} - {profile['blog_title']}",
            archive=archive,
            posts=month_posts,
        )

    public_build_info = {
        "site_name": profile["blog_title"],
        "posts": len(generated_posts),
        "comments": len(generated_comments),
        "environment": environment,
        "generator": "wretch-revival 0.1.0",
    }
    write_json(output_root / "build-info.json", public_build_info)

    report = build_report(posts, comments, generated_posts, generated_comments, output_root)
    report["environment"] = environment
    report["output_path"] = str(output_root)
    write_json(REPORTS_ROOT / f"build-report-{environment}.json", report)
    return report
