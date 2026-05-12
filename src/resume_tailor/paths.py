"""Resolve the repository / deployment root (contains pyproject.toml, input/, web/)."""

from __future__ import annotations

import os
from pathlib import Path


def _is_resume_tailor_repo(dir_path: Path) -> bool:
    pp = dir_path / "pyproject.toml"
    if not pp.is_file():
        return False
    try:
        text = pp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return 'name = "resume_tailor"' in text or "name = 'resume_tailor'" in text


def _find_root_walking_up(start: Path) -> Path | None:
    for base in [start, *start.parents]:
        if _is_resume_tailor_repo(base):
            return base.resolve()
    return None


def project_root() -> Path:
    """
    Used for input/, web/frontend/dist/, output/, and .env when running the API or CLI.

    Order:
    1. RESUME_TAILOR_PROJECT_ROOT if set (required when cwd is wrong and package is installed in site-packages).
    2. Walk up from cwd (Docker WORKDIR=/app finds /app/pyproject.toml).
    3. Walk up from this package directory (editable / src checkout).
    4. Fall back to cwd.
    """
    env = os.getenv("RESUME_TAILOR_PROJECT_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            return p

    found = _find_root_walking_up(Path.cwd().resolve())
    if found:
        return found

    pkg_dir = Path(__file__).resolve().parent
    found = _find_root_walking_up(pkg_dir)
    if found:
        return found

    return Path.cwd().resolve()
