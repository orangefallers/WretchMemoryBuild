#!/usr/bin/env python3
"""Validate a generated public artifact without requiring project dependencies."""

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links = []
        self.inline_scripts = 0
        self.script_sources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"a", "link"} and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "img" and attrs.get("src"):
            self.links.append(attrs["src"])
        if tag == "script":
            if attrs.get("src"):
                self.links.append(attrs["src"])
                self.script_sources.append(attrs["src"])
            else:
                self.inline_scripts += 1


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist/production").resolve()
    required = [root / "index.html", root / "build-info.json", root / ".nojekyll"]
    missing_required = [str(path) for path in required if not path.exists()]
    if missing_required:
        print("Missing required production files:", *missing_required, sep="\n- ")
        return 1

    build_info = json.loads((root / "build-info.json").read_text(encoding="utf-8"))
    if build_info.get("environment") != "production":
        print("build-info.json is not a production build")
        return 1

    pages = sorted(root.rglob("*.html"))
    broken = []
    forbidden = []
    checked_links = 0
    for page in pages:
        content = page.read_text(encoding="utf-8")
        lowered = content.lower()
        for marker in ("wretch.yimg.com", "javascript:"):
            if marker in lowered:
                forbidden.append((str(page.relative_to(root)), marker))

        collector = LinkCollector()
        collector.feed(content)
        if collector.inline_scripts:
            forbidden.append((str(page.relative_to(root)), "inline script"))
        for source in collector.script_sources:
            if urlsplit(source).scheme or source.startswith("//"):
                forbidden.append((str(page.relative_to(root)), "remote script"))
        for value in collector.links:
            parsed = urlsplit(value)
            if parsed.scheme or value.startswith(("#", "mailto:", "tel:")):
                continue
            target = (page.parent / parsed.path).resolve()
            if not str(target).startswith(str(root)):
                broken.append((str(page.relative_to(root)), value, "outside artifact"))
                continue
            if parsed.path.endswith("/") or target.is_dir():
                target = target / "index.html"
            checked_links += 1
            if not target.exists():
                broken.append((str(page.relative_to(root)), value, str(target)))

    if forbidden:
        print("Forbidden production content:", *forbidden[:20], sep="\n- ")
        return 1
    if broken:
        print("Broken production links:", *broken[:20], sep="\n- ")
        return 1

    print(
        json.dumps(
            {
                "environment": "production",
                "html_pages": len(pages),
                "local_links_checked": checked_links,
                "posts": build_info.get("posts"),
                "comments": build_info.get("comments"),
                "valid": True,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
