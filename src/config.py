"""Platform config loader.

The whole platform uses a single yaml file at configs/platform.yaml.
Components import `load_config()` and pull what they need.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class FeatureStoreCfg(BaseModel):
    provider: str = "feast"
    registry: str
    online_store: dict
    offline_store: dict


class RegistryCfg(BaseModel):
    type: str = "mlflow"
    tracking_uri: str
    s3_artifact_root: str
    promotion: dict


class OrchestratorCfg(BaseModel):
    type: str = "prefect"
    api_url: str
    default_work_pool: str = "mlops-pool"


class ServingCfg(BaseModel):
    type: str = "kserve"
    namespace: str
    default_runtime: str


class MonitoringCfg(BaseModel):
    prometheus_pushgateway: str
    drift: dict
    grafana_url: str


class DashboardCfg(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080


class ProjectCfg(BaseModel):
    name: str
    target: str
    feature_view: str
    objective: str


class PlatformCfg(BaseModel):
    name: str = "mlops-platform"
    env: str = "dev"
    region: str = "us-east-1"


class Config(BaseModel):
    platform: PlatformCfg
    feature_store: FeatureStoreCfg
    registry: RegistryCfg
    orchestrator: OrchestratorCfg
    serving: ServingCfg
    monitoring: MonitoringCfg
    dashboard: DashboardCfg
    projects: list[ProjectCfg] = Field(default_factory=list)


DEFAULT_PATH = Path(__file__).resolve().parents[1] / "configs" / "platform.yaml"


@lru_cache(maxsize=1)
def load_config(path: str | os.PathLike | None = None) -> Config:
    p = Path(path) if path else DEFAULT_PATH
    with open(p) as f:
        raw = yaml.safe_load(f)
    return Config(**raw)


def reset_cache() -> None:
    load_config.cache_clear()
