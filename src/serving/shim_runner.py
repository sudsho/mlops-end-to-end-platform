"""Mount one shim app per project under a single uvicorn process."""
from __future__ import annotations

import os

from fastapi import FastAPI

from .shim import build_app

app = FastAPI(title="kserve-shim")

projects = [p.strip() for p in os.environ.get("MLOPS_SHIM_PROJECTS", "").split(",") if p.strip()]

for project in projects:
    transformer = os.environ.get(
        f"MLOPS_SHIM_TRANSFORMER_{project.upper()}",
        f"examples.{project}.serving_transformer",
    )
    try:
        app.mount(f"/{project}", build_app(project, transformer))
    except Exception as e:  # don't take the whole shim down for one bad project
        print(f"shim: skipping {project}: {e}")


@app.get("/")
def index() -> dict:
    return {"projects": projects}
