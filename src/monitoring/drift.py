"""Data drift detection.

Computes a single drift score in [0,1] (share of features that drift).
Above the configured threshold the orchestrator triggers retraining.

Primary backend is Evidently. When Evidently is not installed (it is a
heavy optional dependency) we fall back to a plain per-feature
Kolmogorov-Smirnov / chi-square test using scipy, so the drift codepath
still runs offline with only pandas + scipy present.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _evidently_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("evidently") is not None


def _ks_drift_score(reference: pd.DataFrame, current: pd.DataFrame,
                    p_threshold: float = 0.05) -> float:
    """Share of shared columns whose distribution shifts significantly.

    Numeric columns use a two-sample KS test; categorical columns use a
    chi-square test on the category frequencies. A column counts as
    drifted when its p-value falls below ``p_threshold``.
    """
    from scipy import stats

    cols = [c for c in reference.columns if c in current.columns]
    if not cols:
        return 0.0

    drifted = 0
    counted = 0
    for col in cols:
        ref = reference[col].dropna()
        cur = current[col].dropna()
        if ref.empty or cur.empty:
            continue
        counted += 1
        if pd.api.types.is_numeric_dtype(ref) and pd.api.types.is_numeric_dtype(cur):
            _, p = stats.ks_2samp(ref, cur)
        else:
            cats = sorted(set(ref.astype(str)) | set(cur.astype(str)))
            ref_counts = ref.astype(str).value_counts().reindex(cats, fill_value=0)
            cur_counts = cur.astype(str).value_counts().reindex(cats, fill_value=0)
            # scale current to reference total so chi-square compares shapes
            scale = ref_counts.sum() / max(cur_counts.sum(), 1)
            expected = (cur_counts * scale).clip(lower=1e-9)
            try:
                _, p = stats.chisquare(f_obs=ref_counts + 1e-9, f_exp=expected)
            except Exception:
                p = 1.0
        if p < p_threshold:
            drifted += 1

    if counted == 0:
        return 0.0
    return float(drifted / counted)


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
    ref = reference if reference is not None else _load_reference(project)
    cur = current if current is not None else _load_current(project)

    if not _evidently_available():
        logger.info("evidently not installed, using KS/chi-square drift fallback")
        return _ks_drift_score(ref, cur)

    from evidently import Report
    from evidently.presets import DataDriftPreset

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


def write_drift_report_html(project: str, out_path: str,
                            reference: Optional[pd.DataFrame] = None,
                            current: Optional[pd.DataFrame] = None) -> None:
    ref = reference if reference is not None else _load_reference(project)
    cur = current if current is not None else _load_current(project)

    if not _evidently_available():
        score = _ks_drift_score(ref, cur)
        html = (
            "<html><head><meta charset='utf-8'><title>drift report</title></head>"
            f"<body><h2>Drift report: {project}</h2>"
            "<p>Backend: KS / chi-square fallback (Evidently not installed).</p>"
            f"<p>Share of drifted features: <b>{score:.3f}</b></p>"
            f"<p>Reference rows: {len(ref)}, current rows: {len(cur)}</p>"
            "</body></html>"
        )
        Path(out_path).write_text(html, encoding="utf-8")
        logger.info("wrote fallback drift report to %s", out_path)
        return

    from evidently import Report
    from evidently.presets import DataDriftPreset

    report = Report(metrics=[DataDriftPreset()])
    snap = report.run(reference_data=ref, current_data=cur)
    snap.save_html(out_path)
    logger.info("wrote drift report to %s", out_path)
