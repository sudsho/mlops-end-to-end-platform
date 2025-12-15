"""Streamlit alternative to the FastAPI dashboard.

Run with:  streamlit run src/dashboard/streamlit_app.py
"""
from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from config import load_config


def _project_status(name: str) -> dict:
    try:
        from registry.client import _client
        cli = _client()
        exps = [e for e in cli.search_experiments() if e.name == name]
        if not exps:
            return {"status": "no experiment"}
        runs = cli.search_runs(experiment_ids=[exps[0].experiment_id], max_results=1,
                               order_by=["attributes.start_time DESC"])
        if not runs:
            return {"status": "no runs"}
        r = runs[0]
        return {
            "run_id": r.info.run_id,
            "metrics": dict(r.data.metrics),
            "started": datetime.utcfromtimestamp(r.info.start_time / 1000).isoformat(),
        }
    except Exception as exc:
        return {"status": f"mlflow unreachable: {exc}"}


def main() -> None:
    st.set_page_config(page_title="mlops platform", layout="wide")
    cfg = load_config()
    st.title(f"{cfg.platform.name}")
    st.caption(f"env={cfg.platform.env}  region={cfg.platform.region}")

    rows = []
    for p in cfg.projects:
        s = _project_status(p.name)
        rows.append({
            "project": p.name,
            "objective": p.objective,
            "feature_view": p.feature_view,
            "status": s.get("status") or "ok",
            "latest_metrics": json.dumps(s.get("metrics", {}), default=str),
        })
    st.subheader("projects")
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("backing services")
    st.json({
        "feature_store": cfg.feature_store.model_dump(),
        "registry": cfg.registry.model_dump(),
        "orchestrator": cfg.orchestrator.model_dump(),
        "serving": cfg.serving.model_dump(),
        "monitoring": cfg.monitoring.model_dump(),
    })


if __name__ == "__main__":
    main()
