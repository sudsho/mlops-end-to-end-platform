"""Thin wrapper over Feast for the platform.

Why a wrapper? We want to:
  - keep one codepath that knows where the registry / online store live
  - centralise materialise calls so the orchestrator can use them
  - hide a few feast imports that are heavy and slow to import in cli code
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_repo_path(project: str) -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / project / "feature_repo"


def get_store(project: str):
    """Return a feast FeatureStore for the given project."""
    from feast import FeatureStore

    repo = _get_repo_path(project)
    if not repo.exists():
        raise FileNotFoundError(f"feature repo missing at {repo}")
    return FeatureStore(repo_path=str(repo))


def get_online_features(project: str, feature_view: str, entity_rows: list[dict]) -> dict:
    """Return online features as plain dicts."""
    fs = get_store(project)
    feature_refs = [f"{feature_view}:{f}" for f in fs.get_feature_view(feature_view).features]
    res = fs.get_online_features(features=feature_refs, entity_rows=entity_rows).to_dict()
    return res


def materialize(project: str, hours: int = 1) -> None:
    fs = get_store(project)
    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    logger.info("materialising %s from %s to %s", project, start, end)
    fs.materialize(start_date=start, end_date=end)
