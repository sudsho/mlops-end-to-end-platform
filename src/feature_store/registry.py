"""Cross-project feast registry helpers.

The platform has a SQL-backed feast registry shared across all
projects. We can list known feature views from python without going
through the cli, which the dashboard uses.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


def list_known_projects() -> list[str]:
    examples = Path(__file__).resolve().parents[2] / "examples"
    return sorted([
        p.name for p in examples.iterdir()
        if p.is_dir() and (p / "feature_repo" / "feature_store.yaml").exists()
    ])


def apply_all() -> dict[str, bool]:
    """Run `feast apply` for every example project."""
    import subprocess

    out = {}
    for proj in list_known_projects():
        repo = Path(__file__).resolve().parents[2] / "examples" / proj / "feature_repo"
        try:
            r = subprocess.run(["feast", "apply"], cwd=repo, check=True, capture_output=True)
            out[proj] = True
            logger.info("feast apply for %s ok: %s", proj, r.stdout[:200])
        except subprocess.CalledProcessError as e:
            out[proj] = False
            logger.error("feast apply for %s failed: %s", proj, e.stderr)
    return out
