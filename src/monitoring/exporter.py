"""Prometheus metric exporter.

Two modes:
  - long-running: a /metrics endpoint exposed via FastAPI from the dashboard
  - one-shot: push to the pushgateway from prefect tasks
"""
from __future__ import annotations

import logging
import os
import time
from typing import Iterable

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    push_to_gateway,
)

logger = logging.getLogger(__name__)


# dashboard-side metrics (long-running)
_REG = CollectorRegistry()
TRAIN_RUNS_TOTAL = Counter(
    "mlops_train_runs_total",
    "Number of training runs started.",
    ["project", "status"],
    registry=_REG,
)
DRIFT_SCORE = Gauge(
    "mlops_drift_score",
    "Latest drift score (share of drifted features).",
    ["project"],
    registry=_REG,
)
INFERENCE_LATENCY_S = Histogram(
    "mlops_inference_latency_s",
    "Inference latency seconds.",
    ["project"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=_REG,
)


def get_registry() -> CollectorRegistry:
    return _REG


def push_drift(project: str, score: float) -> None:
    reg = CollectorRegistry()
    g = Gauge("mlops_drift_score", "drift score", ["project"], registry=reg)
    g.labels(project=project).set(score)
    gw = os.environ.get("PROMETHEUS_PUSHGATEWAY", "http://pushgateway:9091")
    try:
        push_to_gateway(gw, job=f"drift-{project}", registry=reg)
    except Exception:
        logger.exception("could not push drift metrics; gateway down?")


def push_run_finished(project: str, status: str = "success") -> None:
    reg = CollectorRegistry()
    c = Counter("mlops_train_runs_total", "training runs", ["project", "status"], registry=reg)
    c.labels(project=project, status=status).inc()
    gw = os.environ.get("PROMETHEUS_PUSHGATEWAY", "http://pushgateway:9091")
    try:
        push_to_gateway(gw, job=f"train-{project}", registry=reg)
    except Exception:
        logger.exception("could not push run metrics")


def push_eval_metric(project: str, metric: str, value: float, run_id: str | None = None) -> None:
    """Push the headline eval metric of a fresh run so grafana can plot it.

    Kept separate from push_run_finished so the counter stays a counter and
    the value stays a gauge with its own job label.
    """
    reg = CollectorRegistry()
    g = Gauge(f"mlops_eval_{metric}", f"latest {metric}", ["project"], registry=reg)
    g.labels(project=project).set(value)
    ts = Gauge("mlops_eval_pushed_at", "unix ts of last metric push", ["project"], registry=reg)
    ts.labels(project=project).set(time.time())
    gw = os.environ.get("PROMETHEUS_PUSHGATEWAY", "http://pushgateway:9091")
    job = f"eval-{project}" if run_id is None else f"eval-{project}-{run_id[:8]}"
    try:
        push_to_gateway(gw, job=job, registry=reg)
    except Exception:
        logger.exception("could not push eval metric")
