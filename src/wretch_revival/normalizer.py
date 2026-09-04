from collections import Counter
from typing import Any, Dict

from .merger import merge_sources
from .mt_parser import parse_mt
from .paths import DATA_ROOT, REPORTS_ROOT, find_backup_file
from .utils import write_json
from .xml_parser import parse_xml


def normalize_backup() -> Dict[str, Any]:
    xml = parse_xml(find_backup_file("*_blog.xml"))
    mt = parse_mt(find_backup_file("*-movable-type.txt"))
    merged = merge_sources(xml, mt)

    tag_counts = Counter(tag for post in merged["posts"] for tag in post["tags"])
    tags = [
        {"name": name, "post_count": count}
        for name, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    write_json(DATA_ROOT / "profile.json", merged["profile"])
    write_json(DATA_ROOT / "posts.json", merged["posts"])
    write_json(DATA_ROOT / "comments.json", merged["comments"])
    write_json(DATA_ROOT / "tags.json", tags)

    if merged["warnings"]:
        REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
        (REPORTS_ROOT / "build-errors.log").write_text(
            "\n".join(f"[WARN] {message}" for message in merged["warnings"]) + "\n",
            encoding="utf-8",
        )
    else:
        log = REPORTS_ROOT / "build-errors.log"
        if log.exists():
            log.unlink()
    return merged

