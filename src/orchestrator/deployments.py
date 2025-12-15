"""Define Prefect deployments for each project.

Run from repo root:  python -m orchestrator.deployments deploy

This builds two deployments per project:
  - <project>-train-daily   : cron'd training run
  - <project>-drift-hourly  : drift check that retrains if over threshold
"""
from __future__ import annotations

import logging

from prefect import deploy, get_client
from prefect.client.schemas.schedules import CronSchedule

from config import load_config
from orchestrator.flows import retrain_on_drift_flow, train_flow

logger = logging.getLogger(__name__)


def build_deployments() -> list[dict]:
    cfg = load_config()
    out = []
    for p in cfg.projects:
        out.append({
            "name": f"{p.name}-train-daily",
            "flow": train_flow,
            "parameters": {"project": p.name},
            "schedule": CronSchedule(cron="0 2 * * *", timezone="UTC"),
            "work_pool": cfg.orchestrator.default_work_pool,
        })
        out.append({
            "name": f"{p.name}-drift-hourly",
            "flow": retrain_on_drift_flow,
            "parameters": {
                "project": p.name,
                "drift_threshold": cfg.monitoring.drift.get("threshold", 0.2),
            },
            "schedule": CronSchedule(cron="0 * * * *", timezone="UTC"),
            "work_pool": cfg.orchestrator.default_work_pool,
        })
    return out


def main() -> None:
    cfgs = build_deployments()
    for d in cfgs:
        flow_obj = d.pop("flow")
        flow_obj.deploy(**d)
        logger.info("deployed %s", d["name"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
