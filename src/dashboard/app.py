"""FastAPI dashboard. Lists projects, latest run, drift, deployment."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from prometheus_client import generate_latest

from config import load_config
from monitoring.exporter import get_registry

app = FastAPI(title="mlops-platform dashboard")

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/healthz", response_class=PlainTextResponse)
def healthz() -> str:
    return "ok"


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(get_registry()).decode("utf-8"))


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    cfg = load_config()
    projects = []
    for p in cfg.projects:
        projects.append({
            "name": p.name,
            "objective": p.objective,
            "feature_view": p.feature_view,
        })
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"projects": projects, "cfg": cfg.platform.model_dump()},
    )


@app.get("/api/projects")
def api_projects() -> dict:
    cfg = load_config()
    return {"projects": [p.model_dump() for p in cfg.projects]}


@app.get("/api/projects/{name}/status")
def project_status(name: str) -> dict:
    """Quick status: latest run id, current drift, current stage."""
    from registry.client import _client as mlflow_client

    cli = mlflow_client()
    runs = cli.search_runs(experiment_ids=[
        e.experiment_id for e in cli.search_experiments() if e.name == name
    ], max_results=1, order_by=["attributes.start_time DESC"])

    latest_run = runs[0] if runs else None
    versions = cli.search_model_versions(f"name='{name}'") if latest_run else []
    return {
        "project": name,
        "latest_run_id": latest_run.info.run_id if latest_run else None,
        "latest_metrics": dict(latest_run.data.metrics) if latest_run else {},
        "deployments": [
            {"version": v.version, "stage": v.current_stage} for v in versions
        ],
    }
