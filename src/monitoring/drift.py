"""Data drift detection via Evidently.

Computes a single drift score in [0,1] (share of features that drift).
Above the configured threshold the orchestrator triggers retraining.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _load_reference(project: str) -> pd.DataFrame:
    p = Path(__file__).resolve().parents[2] / "examples" / project / "data" / "reference.parquet"
    if not p.exists():
        # fall back to csv during early bring-up
        csv = p.with_suffix(".csv")
        return pd.read_csv(csv)
    return pd.read_parquet(p)


def _load_current(project: str) -> pd.DataFrame:
    p = Path(__file__).resolve().parents[2] / "examples" / project / "data" / "current.parquet"
    if not p.exists():
        csv = p.with_suffix(".csv")
        return pd.read_csv(csv)
    return pd.read_parquet(p)


def current_drift_score(project: str,
                        reference: Optional[pd.DataFrame] = None,
                        current: Optional[pd.DataFrame] = None) -> float:
    """Return share-of-drifted-features score in [0,1]."""
    from evidently import Report
    from evidently.presets import DataDriftPreset

    ref = reference if reference is not None else _load_reference(project)
    cur = current if current is not None else _load_current(project)

    report = Report(metrics=[DataDriftPreset()])
    snap = report.run(reference_data=ref, current_data=cur)
    res = snap.dict()

    # Evidently 0.6 returns metrics in res["metrics"]; pull the share-drifted scalar
    for m in res.get("metrics", []):
        if m.get("metric_id", "").startswith("DriftedColumnsCount"):
            val = m.get("value", {})
            share = val.get("share")
            if share is not None:
                return float(share)
    return 0.0


def write_drift_report_html(project: str, out_path: str) -> None:
    from evidently import Report
    from evidently.presets import DataDriftPreset

    ref = _load_reference(project)
    cur = _load_current(project)
    report = Report(metrics=[DataDriftPreset()])
    snap = report.run(reference_data=ref, current_data=cur)
    snap.save_html(out_path)
    logger.info("wrote drift report to %s", out_path)
