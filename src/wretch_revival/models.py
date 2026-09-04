from typing import Optional


PUBLIC = "public"
DRAFT = "draft"
HIDDEN = "hidden"
UNKNOWN = "unknown"


def post_visibility(code: str) -> str:
    return {"0": PUBLIC, "1": HIDDEN, "2": DRAFT}.get(code, UNKNOWN)


def comment_visibility(code: str) -> str:
    return PUBLIC if code == "0" else HIDDEN if code == "1" else UNKNOWN


def is_publishable(visibility: str, include_drafts: bool = False) -> bool:
    return visibility == PUBLIC or include_drafts


def optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None

