"""Render KServe InferenceService YAML for a project."""
from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import load_config
from registry.client import get_latest_model_uri

TEMPLATES = Path(__file__).resolve().parent / "manifests"


def render_inference_service(project: str, *, stage: str = "Staging",
                             min_replicas: int = 1, max_replicas: int = 3) -> str:
    cfg = load_config()
    proj = next(p for p in cfg.projects if p.name == project)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)),
                      autoescape=select_autoescape())
    tpl = env.get_template("inference_service.yaml.j2")
    return tpl.render(
        project=project,
        namespace=cfg.serving.namespace,
        feature_view=proj.feature_view,
        entity_keys=_default_entity_keys(project),
        model_uri=get_latest_model_uri(project, stage=stage),
        mlflow_uri=cfg.registry.tracking_uri,
        pushgateway=cfg.monitoring.prometheus_pushgateway,
        min_replicas=min_replicas,
        max_replicas=max_replicas,
    )


def _default_entity_keys(project: str) -> list[str]:
    return {
        "churn": ["customer_id"],
        "fraud": ["card_id"],
        "recommender": ["user_id", "item_id"],
    }.get(project, ["id"])


def write_inference_service(project: str, out_dir: str, **kwargs) -> str:
    out = Path(out_dir) / f"{project}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_inference_service(project, **kwargs))
    return str(out)
