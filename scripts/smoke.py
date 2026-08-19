"""Offline smoke test for the MLOps platform core lifecycle.

Runs the whole train -> register -> promote -> load -> predict -> drift
loop on synthetic data with local backends only. No Feast, Prefect,
KServe, Postgres, Redis, S3, or a running MLflow server are required.

What it exercises (all with real platform code, not reimplementations):

  1. build features   - synthetic churn frame (plain pandas, Feast stand-in)
  2. train + log       - registry.client.register_run -> local MLflow (file:./mlruns)
  3. register+promote  - registry.policy.promote_if_passes (-> Staging)
                         registry.policy.auto_promote_to_production (-> Production)
  4. load + predict    - mlflow.pyfunc.load_model on the Production URI
  5. drift             - monitoring.drift.current_drift_score on
                         reference-vs-current synthetic frames
                         (Evidently if installed, else KS/chi-square fallback)

Run from the repo root:

    python scripts/smoke.py
    make smoke
"""
from __future__ import annotations

import os
import sys
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Local MLflow: plain file store under the repo, no server needed.
MLRUNS = ROOT / "mlruns"
os.environ["MLFLOW_TRACKING_URI"] = "file:///" + str(MLRUNS).replace("\\", "/")
os.environ.setdefault("MLOPS_ENV", "smoke")

PROJECT = "churn"
# The synthetic churn signal is intentionally weak (GBM lands around
# roc_auc 0.70). The gate sits a little below that so the smoke passes
# reliably across sklearn versions while staying a real quality check.
THRESHOLD = 0.65


def _rule(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    import mlflow

    _rule("0. environment")
    print(f"mlflow tracking uri : {os.environ['MLFLOW_TRACKING_URI']}")
    try:
        import feast  # noqa: F401
        print("feast               : installed")
    except Exception:
        print("feast               : not installed -> pandas feature stand-in")
    try:
        import evidently  # noqa: F401
        print("evidently           : installed")
    except Exception:
        print("evidently           : not installed -> KS/chi-square drift fallback")

    # 1. build features (Feast stand-in: synthetic pandas frame) -------------
    _rule("1. build features (synthetic, Feast stand-in)")
    from examples._data.make_synthetic import churn

    frame = churn(n=4000)
    print(f"built churn frame   : {frame.shape[0]} rows x {frame.shape[1]} cols")
    print(f"positive class rate : {frame['churned'].mean():.3f}")

    # 2. train + log to local MLflow ----------------------------------------
    _rule("2. train + log to local MLflow")
    from registry.client import register_run

    run_id = register_run(project=PROJECT, data_path="synthetic://churn")
    client = mlflow.tracking.MlflowClient()
    metrics = client.get_run(run_id).data.metrics
    print(f"run_id              : {run_id}")
    print(f"roc_auc             : {metrics['roc_auc']:.4f}")
    print(f"accuracy            : {metrics['accuracy']:.4f}")

    # 3. register + promote --------------------------------------------------
    _rule("3. register + promote")
    from registry.policy import auto_promote_to_production, promote_if_passes

    staged = promote_if_passes(PROJECT, run_id=run_id, threshold=THRESHOLD)
    print(f"promoted to Staging : {staged} (threshold roc_auc >= {THRESHOLD})")
    if not staged:
        print("ERROR: model did not pass the promotion gate")
        return 1
    # min_staging_hours=0 so the freshly staged model is eligible right away
    produced = auto_promote_to_production(PROJECT, min_staging_hours=0)
    print(f"promoted to Prod    : {produced}")
    if not produced:
        print("ERROR: model was not promoted to Production")
        return 1

    # 4. load back + predict -------------------------------------------------
    _rule("4. load Production model + predict")
    from registry.client import get_latest_model_uri

    uri = get_latest_model_uri(PROJECT, stage="Production")
    print(f"model uri           : {uri}")
    model = mlflow.pyfunc.load_model(uri)

    from examples.churn.train import CAT, NUM

    sample = frame[CAT + NUM].head(5)
    preds = model.predict(sample)
    print(f"predictions (5 rows): {[int(x) for x in preds]}")

    # 5. drift report --------------------------------------------------------
    _rule("5. drift: reference vs current (synthetic)")
    from monitoring.drift import current_drift_score, write_drift_report_html

    reference = churn(n=2000)
    current = churn(n=2000).copy()
    # inject drift: shift the numeric charge features
    current["monthly_charges"] = current["monthly_charges"] * 1.6 + 25
    current["total_charges"] = current["total_charges"] * 1.4 + 500

    feat_cols = CAT + NUM
    no_drift = current_drift_score(PROJECT, reference=reference[feat_cols],
                                   current=reference[feat_cols])
    with_drift = current_drift_score(PROJECT, reference=reference[feat_cols],
                                     current=current[feat_cols])
    print(f"drift (ref vs ref)  : {no_drift:.3f}")
    print(f"drift (ref vs cur)  : {with_drift:.3f}")

    out_html = ROOT / "artifacts" / "drift_report.html"
    out_html.parent.mkdir(parents=True, exist_ok=True)
    write_drift_report_html(PROJECT, str(out_html),
                            reference=reference[feat_cols],
                            current=current[feat_cols])
    print(f"drift report        : {out_html.relative_to(ROOT)}")

    # summary ----------------------------------------------------------------
    _rule("SMOKE OK")
    ok = (
        metrics["roc_auc"] >= THRESHOLD
        and staged
        and produced
        and no_drift <= with_drift
        and with_drift > 0.0
    )
    print(f"roc_auc >= {THRESHOLD}       : {metrics['roc_auc'] >= THRESHOLD}")
    print(f"staged + produced   : {staged and produced}")
    print(f"drift detected      : {with_drift > no_drift}")
    print(f"\nRESULT              : {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
