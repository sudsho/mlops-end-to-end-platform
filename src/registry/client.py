"""MLflow client wrappers used by the platform.

Two surfaces:
 - register_run(...) starts a run, trains, logs metrics + the model
 - get_latest_model_uri(project, stage) returns the URI to load
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _client():
    from mlflow.tracking import MlflowClient

    uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    return MlflowClient(tracking_uri=uri)


def register_run(project: str, data_path: str, params: dict[str, Any] | None = None) -> str:
    """Train (delegated to project's train.py) and log to MLflow.

    Returns the mlflow run_id.
    """
    import importlib

    import mlflow

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
    mlflow.set_experiment(project)
    train_mod = importlib.import_module(f"examples.{project}.train")

    with mlflow.start_run() as run:
        run_id = run.info.run_id
        mlflow.log_param("data_path", data_path)
        for k, v in (params or {}).items():
            mlflow.log_param(k, v)
        out = train_mod.train(data_path=data_path)  # type: ignore[attr-defined]
        for k, v in out.metrics.items():
            mlflow.log_metric(k, v)
        mlflow.sklearn.log_model(
            sk_model=out.model,
            artifact_path="model",
            registered_model_name=project,
        )
    return run_id


def get_latest_model_uri(project: str, stage: str = "Production") -> str:
    cli = _client()
    versions = cli.get_latest_versions(name=project, stages=[stage])
    if not versions:
        raise LookupError(f"no model in {stage} for {project}")
    return f"models:/{project}/{versions[0].version}"
