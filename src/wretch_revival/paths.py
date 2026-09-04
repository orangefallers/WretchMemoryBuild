from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKUP_ROOT = PROJECT_ROOT / "backup" / "original"
CONFIG_ROOT = PROJECT_ROOT / "config"
DATA_ROOT = PROJECT_ROOT / "data"
REPORTS_ROOT = PROJECT_ROOT / "reports"
TEMPLATES_ROOT = PROJECT_ROOT / "templates"
STATIC_ROOT = PROJECT_ROOT / "static"
DIST_ROOT = PROJECT_ROOT / "dist"
LOCAL_DIST_ROOT = DIST_ROOT / "local"
PRODUCTION_DIST_ROOT = DIST_ROOT / "production"


def find_backup_file(pattern: str) -> Path:
    matches = sorted(BACKUP_ROOT.rglob(pattern))
    if not matches:
        raise FileNotFoundError(f"在 {BACKUP_ROOT} 找不到 {pattern}")
    if len(matches) > 1:
        raise RuntimeError(f"找到多個 {pattern}，無法判斷來源：{matches}")
    return matches[0]
