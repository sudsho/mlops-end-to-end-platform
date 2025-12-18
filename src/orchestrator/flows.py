"""Prefect 3 flows for training and retraining.

Flow names match the project name. Run on demand from the cli or on a
schedule via prefect deployments (see scripts/deploy.sh).
"""
from __future__ import annotations

import logging
from typing import Any

from prefect import flow, get_run_logger, task

logger = logging.getLogger(__name__)


@task(retries=2, retry_delay_seconds=10)
def materialize_features(project: str, hours: int = 24) -> None:
    from feature_store.store import materialize

    materialize(project, hours=hours)


@task
def fetch_training_data(project: str) -> dict[str, Any]:
    """Pull historical features + labels for the project."""
    # In production this calls feast.get_historical_features. Here we return
    # a path placeholder so the train task can pick up the parquet.
    return {"path": f"data/{project}/train.parquet"}


@task
def train_model(project: str, data_path: str) -> str:
    from registry.client import register_run

    run_id = register_run(project=project, data_path=data_path)
    return run_id


@task
def evaluate_and_promote(project: str, run_id: str, threshold: float) -> bool:
    from registry.policy import promote_if_passes

    return promote_if_passes(project=project, run_id=run_id, threshold=threshold)


@flow(name="train")
def train_flow(project: str, threshold: float = 0.7) -> dict[str, Any]:
    log = get_run_logger()
    log.info("training flow start project=%s", project)

    materialize_features(project, hours=24)
    data = fetch_training_data(project)
    run_id = train_model(project, data["path"])
    promoted = evaluate_and_promote(project, run_id, threshold)

    return {"project": project, "run_id": run_id, "promoted": promoted}


@flow(name="retrain-on-drift")
def retrain_on_drift_flow(project: str, drift_threshold: float = 0.2) -> dict[str, Any]:
    from monitoring.drift import current_drift_score
    from monitoring.exporter import push_drift

    log = get_run_logger()
    score = current_drift_score(project)
    push_drift(project, score)
    log.info("drift score for %s = %.3f", project, score)
    if score < drift_threshold:
        return {"project": project, "retrained": False, "drift": score}

    log.warning("drift over threshold, retraining %s", project)
    out = train_flow(project)
    out["drift"] = score
    out["retrained"] = True
    return out


@flow(name="batch-score")
def batch_score_flow(project: str, input_path: str, output_path: str) -> dict[str, Any]:
    """Run a batch scoring job using the latest Production model."""
    import pandas as pd
    import mlflow.pyfunc

    from registry.client import get_latest_model_uri

    log = get_run_logger()
    uri = get_latest_model_uri(project, stage="Production")
    log.info("loading model %s", uri)
    model = mlflow.pyfunc.load_model(uri)
    df = pd.read_parquet(input_path)
    df["score"] = model.predict(df)
    df.to_parquet(output_path, index=False)
    return {"project": project, "rows": len(df), "out": output_path}
