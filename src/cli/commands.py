"""Backing implementations for the CLI commands.

Kept separate from main.py so these are unit-testable without going
through Click.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def cmd_project_new(name: str) -> dict[str, Any]:
    """Create a new project under examples/<name> with the standard layout."""
    target = ROOT / "examples" / name
    if target.exists():
        return {"name": name, "ok": False, "reason": "already exists"}

    (target / "feature_repo").mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(parents=True, exist_ok=True)

    (target / "README.md").write_text(f"# {name}\n\nTODO: describe project.\n")
    (target / "feature_definitions.py").write_text(
        '"""TODO: define feast entities and feature views."""\n'
    )
    (target / "train.py").write_text(
        '"""TODO: load features, train model, return Result(model, metrics)."""\n'
    )
    return {"name": name, "ok": True, "path": str(target)}


def cmd_train(project: str) -> dict[str, Any]:
    from orchestrator.flows import train_flow
    return train_flow(project)


def cmd_register(project: str, run_id: str | None, metric: str, threshold: float) -> dict[str, Any]:
    from registry.policy import promote_if_passes

    if run_id is None:
        # use latest run for that experiment
        from registry.client import _client
        cli = _client()
        exps = [e for e in cli.search_experiments() if e.name == project]
        if not exps:
            return {"ok": False, "reason": f"no experiment named {project}"}
        runs = cli.search_runs(experiment_ids=[exps[0].experiment_id], max_results=1,
                               order_by=["attributes.start_time DESC"])
        if not runs:
            return {"ok": False, "reason": "no runs"}
        run_id = runs[0].info.run_id

    promoted = promote_if_passes(project=project, run_id=run_id,
                                 threshold=threshold, metric_name=metric)
    return {"ok": True, "promoted": promoted, "run_id": run_id}


def cmd_deploy(project: str, target: str) -> dict[str, Any]:
    from serving.render import write_inference_service

    out_dir = ROOT / "build" / "manifests"
    p = write_inference_service(project, str(out_dir),
                                stage="Production" if target == "production" else "Staging")
    # In a real cluster, kubectl apply -f. We render and let scripts/deploy.sh apply.
    return {"ok": True, "manifest": p, "target": target}


def cmd_drift(project: str) -> dict[str, Any]:
    from monitoring.drift import current_drift_score
    from monitoring.exporter import push_drift

    score = current_drift_score(project)
    push_drift(project, score)
    return {"project": project, "drift": score}
