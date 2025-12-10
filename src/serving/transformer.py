"""KServe Transformer.

Sits in front of the predictor. On each request, looks up online
features from feast for the entity in the body, attaches them, and
forwards to the predictor. After the predictor responds, records the
inference latency to Prometheus.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


class FeatureLookupTransformer:
    """KServe v2 protocol transformer."""

    def __init__(self, project: str, feature_view: str, entity_keys: list[str]) -> None:
        self.project = project
        self.feature_view = feature_view
        self.entity_keys = entity_keys

    def preprocess(self, payload: dict[str, Any], headers: dict | None = None) -> dict[str, Any]:
        from feature_store.store import get_online_features
        from monitoring.exporter import INFERENCE_LATENCY_S

        instances = payload.get("instances") or payload.get("inputs", [])
        entity_rows = [
            {k: inst[k] for k in self.entity_keys if k in inst}
            for inst in instances
        ]
        feats = get_online_features(self.project, self.feature_view, entity_rows)
        merged = []
        for i, inst in enumerate(instances):
            row = dict(inst)
            for k, vs in feats.items():
                row[k] = vs[i]
            merged.append(row)
        # remember when we started so postprocess can measure
        self._t0 = time.perf_counter()
        return {"instances": merged}

    def postprocess(self, response: dict[str, Any], headers: dict | None = None) -> dict[str, Any]:
        from monitoring.exporter import INFERENCE_LATENCY_S

        elapsed = time.perf_counter() - getattr(self, "_t0", time.perf_counter())
        try:
            INFERENCE_LATENCY_S.labels(project=self.project).observe(elapsed)
        except Exception:
            pass
        return response
