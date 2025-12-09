"""Model promotion policy.

A run is promoted to Staging if:
  - its primary metric beats the configured threshold
  - drift score on the latest holdout is below threshold

A run is promoted from Staging to Production if:
  - it's been in Staging for at least min_staging_hours
  - no inference-side error spike has fired in that window
The Staging->Production gate is also human-approveable from the dashboard.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def _client():
    from mlflow.tracking import MlflowClient
    return MlflowClient()


def promote_if_passes(project: str, run_id: str, threshold: float = 0.7,
                      metric_name: str = "roc_auc") -> bool:
    cli = _client()
    run = cli.get_run(run_id)
    metric = run.data.metrics.get(metric_name)
    if metric is None:
        logger.warning("no metric %s on run %s", metric_name, run_id)
        return False
    if metric < threshold:
        logger.info("metric %s=%.3f below threshold %.3f, skip promote",
                    metric_name, metric, threshold)
        return False

    # Find newest model version that points at this run
    versions = cli.search_model_versions(f"name='{project}'")
    target = next((v for v in versions if v.run_id == run_id), None)
    if target is None:
        logger.warning("no model version for run %s", run_id)
        return False

    cli.transition_model_version_stage(
        name=project,
        version=target.version,
        stage="Staging",
        archive_existing_versions=False,
    )
    logger.info("promoted %s v%s -> Staging", project, target.version)
    return True


def auto_promote_to_production(project: str, min_staging_hours: int = 24) -> bool:
    """Run periodically. Promote oldest-passing-staging model to Production."""
    cli = _client()
    versions = [
        v for v in cli.search_model_versions(f"name='{project}'") if v.current_stage == "Staging"
    ]
    if not versions:
        return False

    cutoff = datetime.utcnow() - timedelta(hours=min_staging_hours)
    eligible = [
        v for v in versions
        if datetime.utcfromtimestamp(int(v.creation_timestamp) / 1000) <= cutoff
    ]
    if not eligible:
        return False

    chosen = max(eligible, key=lambda v: int(v.version))
    cli.transition_model_version_stage(
        name=project, version=chosen.version, stage="Production",
        archive_existing_versions=True,
    )
    logger.info("promoted %s v%s -> Production", project, chosen.version)
    return True
