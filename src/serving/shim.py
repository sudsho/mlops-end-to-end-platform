"""Local fallback for KServe.

When there is no kube cluster around (laptop / CI / smoke test) we still
want `mlops deploy` to land somewhere predictable. This module spins up a
small FastAPI app per project that mimics the V2 inference protocol.

It is NOT a replacement for KServe in prod. The point is to keep the dev
loop short. To actually mount a project the transformer module at
`examples.<project>.serving_transformer` must exist and expose `predict`;
this repo does not ship one, so the local shim starts empty by default.
"""
from __future__ import annotations

import importlib
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

log = logging.getLogger(__name__)


class V2InferRequest(BaseModel):
    inputs: list[dict[str, Any]]


class V2InferResponse(BaseModel):
    model_name: str
    outputs: list[dict[str, Any]]


def build_app(project: str, transformer_module: str) -> FastAPI:
    """Build a tiny FastAPI app that wraps a project's transformer.

    `transformer_module` is the dotted path the deploy renderer wrote
    into the manifest's TRANSFORMER env var, e.g.
    `examples.churn.serving_transformer`.
    """
    app = FastAPI(title=f"kserve-shim::{project}")
    mod = importlib.import_module(transformer_module)
    if not hasattr(mod, "predict"):
        raise RuntimeError(f"{transformer_module} has no predict()")

    @app.get("/v2/health/ready")
    def ready() -> dict[str, bool]:
        return {"ready": True}

    @app.post(f"/v2/models/{project}/infer", response_model=V2InferResponse)
    def infer(req: V2InferRequest) -> V2InferResponse:
        try:
            outs = [mod.predict(inp) for inp in req.inputs]
        except Exception as e:  # surface as 4xx so the dashboard doesn't go red on a bad payload
            log.warning("infer failed for %s: %s", project, e)
            raise HTTPException(status_code=400, detail=str(e))
        return V2InferResponse(model_name=project, outputs=outs)

    return app
