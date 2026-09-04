import argparse
import json
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Sequence

from .builder import build_site
from .normalizer import normalize_backup
from .paths import DIST_ROOT
from .scanner import inspect_backup


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _build(environment: str = "local") -> dict:
    inspect_backup(write_report=True)
    merged = normalize_backup()
    return build_site(merged, environment=environment)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="重建無名小站 Blog 靜態網站")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect", help="分析備份完整度")
    subparsers.add_parser("import", help="產生標準化 JSON")
    build = subparsers.add_parser("build", help="產生靜態網站")
    build.add_argument("--environment", choices=("local", "production"), default="local")
    serve = subparsers.add_parser("serve", help="建置並啟動本機預覽")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = create_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _print(inspect_backup(write_report=True))
        elif args.command == "import":
            merged = normalize_backup()
            _print(
                {
                    "posts": len(merged["posts"]),
                    "comments": len(merged["comments"]),
                    "warnings": len(merged["warnings"]),
                }
            )
        elif args.command == "build":
            _print(_build(args.environment))
        elif args.command == "serve":
            report = _build("local")
            if not report["build_success"]:
                raise RuntimeError("完整性檢查失敗，未啟動預覽")
            handler = partial(SimpleHTTPRequestHandler, directory=str(DIST_ROOT / "local"))
            server = ThreadingHTTPServer((args.host, args.port), handler)
            print(f"本機預覽：http://{args.host}:{args.port}")
            server.serve_forever()
    except KeyboardInterrupt:
        print("\n預覽已停止")
    except Exception as error:
        print(f"錯誤：{error}", file=sys.stderr)
        raise SystemExit(2) from error
