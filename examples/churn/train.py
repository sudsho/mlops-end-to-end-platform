"""Churn training. Returns a Result(model, metrics).

Loaded by registry.client.register_run via importlib.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class Result:
    model: Any
    metrics: dict[str, float]


CAT = ["contract_type", "internet_service", "payment_method"]
NUM = ["tenure_months", "monthly_charges", "total_charges",
       "num_support_calls_30d", "num_late_payments_90d",
       "auto_pay", "paperless_billing"]


def _build_pipeline() -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ("num", StandardScaler(), NUM),
    ])
    return Pipeline([
        ("pre", pre),
        ("clf", GradientBoostingClassifier(n_estimators=120, max_depth=3, random_state=42)),
    ])


def train(data_path: str | None = None) -> Result:
    if data_path and Path(data_path).exists():
        df = pd.read_parquet(data_path)
    else:
        # demo path: regenerate inline
        from examples._data.make_synthetic import churn
        df = churn(n=4000)

    y = df["churned"].astype(int)
    X = df[CAT + NUM]

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipe = _build_pipeline()
    pipe.fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]
    pred = (proba > 0.5).astype(int)
    return Result(
        model=pipe,
        metrics={
            "roc_auc": float(roc_auc_score(yte, proba)),
            "accuracy": float(accuracy_score(yte, pred)),
            "n_train": len(Xtr),
        },
    )


if __name__ == "__main__":
    r = train()
    print(r.metrics)
