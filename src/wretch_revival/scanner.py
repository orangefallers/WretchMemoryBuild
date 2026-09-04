from collections import Counter
from pathlib import Path
from typing import Any, Dict

from .mt_parser import parse_mt
from .paths import BACKUP_ROOT, REPORTS_ROOT, find_backup_file
from .utils import write_json
from .xml_parser import parse_xml


def inspect_backup(write_report: bool = True) -> Dict[str, Any]:
    xml_path = find_backup_file("*_blog.xml")
    mt_path = find_backup_file("*-movable-type.txt")
    xml = parse_xml(xml_path)
    mt = parse_mt(mt_path)

    files = [path for path in BACKUP_ROOT.rglob("*") if path.is_file()]
    extensions = Counter((path.suffix.lower() or "[none]") for path in files)
    post_ids = {post["id"] for post in xml["posts"]}
    orphan_comments = sum(comment["post_id"] not in post_ids for comment in xml["comments"])
    visible_comments_on_public_posts = sum(
        comment["visibility"] == "public"
        and next(
            (post["visibility"] for post in xml["posts"] if post["id"] == comment["post_id"]),
            None,
        )
        == "public"
        for comment in xml["comments"]
    )

    report = {
        "backup_root": str(BACKUP_ROOT),
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "extensions": dict(sorted(extensions.items())),
        "xml_source": xml["source"],
        "mt_source": mt["source"],
        "posts": len(xml["posts"]),
        "posts_declared": xml["profile"]["declared_post_count"],
        "posts_public": sum(post["visibility"] == "public" for post in xml["posts"]),
        "posts_non_public": sum(post["visibility"] != "public" for post in xml["posts"]),
        "comments": len(xml["comments"]),
        "comments_declared": xml["profile"]["declared_comment_count"],
        "comments_public": sum(comment["visibility"] == "public" for comment in xml["comments"]),
        "comments_hidden": sum(comment["visibility"] != "public" for comment in xml["comments"]),
        "comments_public_on_public_posts": visible_comments_on_public_posts,
        "orphan_comments": orphan_comments,
        "mt_posts": len(mt["posts"]),
        "mt_comments": mt["comment_count"],
        "encoding": "UTF-8",
    }
    report["sufficient_for_article_mvp"] = (
        report["posts"] == report["posts_declared"] == report["mt_posts"]
        and report["comments"] == report["comments_declared"]
        and report["orphan_comments"] == 0
    )
    if write_report:
        write_json(REPORTS_ROOT / "backup-report.json", report)
    return report
