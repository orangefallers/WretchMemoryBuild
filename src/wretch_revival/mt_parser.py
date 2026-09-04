import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List

from .utils import mt_date_to_iso, sha256_file


ENTRY_SEPARATOR = re.compile(r"(?m)^--------\s*$")
SECTION_SEPARATOR = re.compile(r"(?m)^-----\s*$")


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


def _header_value(header: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}:\s*(.*)$", header)
    return match.group(1).strip() if match else ""


def _parse_tags(raw: str) -> List[str]:
    tags: List[str] = []
    for value in raw.split(","):
        value = value.strip()
        if value and value not in tags:
            tags.append(value)
    return tags


def parse_mt(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    entries: List[Dict[str, Any]] = []
    total_comments = 0

    for raw_entry in ENTRY_SEPARATOR.split(text):
        entry = raw_entry.strip("\r\n")
        if not entry.lstrip().startswith("TITLE:"):
            continue

        sections = SECTION_SEPARATOR.split(entry)
        header = sections[0]
        body = ""
        comments = 0
        for section in sections[1:]:
            section = section.strip("\r\n")
            if section.startswith("BODY:"):
                body = section[len("BODY:") :].lstrip("\r\n").rstrip()
            elif section.startswith("COMMENT:"):
                comments += 1

        scanner = _ImageScanner()
        scanner.feed(body)
        record = {
            "title": _header_value(header, "TITLE"),
            "author": _header_value(header, "AUTHOR"),
            "date": mt_date_to_iso(_header_value(header, "DATE")),
            "status": _header_value(header, "STATUS").lower(),
            "tags": _parse_tags(_header_value(header, "TAGS")),
            "content_html": body,
            "image_urls": scanner.sources,
            "comment_count": comments,
        }
        entries.append(record)
        total_comments += comments

    return {
        "source": {"path": str(path), "sha256": sha256_file(path)},
        "posts": entries,
        "comment_count": total_comments,
        "status_counts": dict(Counter(entry["status"] for entry in entries)),
    }

