import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional


TAIPEI_TZ = timezone(timedelta(hours=8))


def to_iso(value: Optional[str], source_format: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if not value or value.startswith("0000-00-00"):
        return None
    return datetime.strptime(value, source_format).replace(tzinfo=TAIPEI_TZ).isoformat()


def mt_date_to_iso(value: Optional[str]) -> Optional[str]:
    return to_iso(value, "%m/%d/%Y %H:%M:%S")


def compact_date(value: str) -> str:
    dt = datetime.fromisoformat(value)
    return dt.strftime("%Y%m%d")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(value: str) -> str:
    name = Path(value).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)
