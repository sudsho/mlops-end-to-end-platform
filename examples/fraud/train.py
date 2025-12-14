"""Fraud training. Logistic regression baseline + class weight."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class Result:
    model: Any
    metrics: dict[str, float]


CAT = ["merchant_category"]
NUM = ["amount", "amount_zscore_1h", "num_tx_1h", "num_unique_merchants_1h",
       "time_since_last_tx_s", "card_present", "cross_border"]


def _build_pipeline() -> Pipeline:
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ("num", StandardScaler(), NUM),
    ])
    return Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=None)),
    ])


def train(data_path: str | None = None) -> Result:
    if data_path and Path(data_path).exists():
        df = pd.read_parquet(data_path)
    else:
        from examples._data.make_synthetic import fraud
        df = fraud(n=8000)

    y = df["is_fraud"].astype(int)
    X = df[CAT + NUM]

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=7)
    pipe = _build_pipeline()
    pipe.fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]
    return Result(
        model=pipe,
        metrics={
            "roc_auc": float(roc_auc_score(yte, proba)),
            "pr_auc": float(average_precision_score(yte, proba)),
            "n_train": len(Xtr),
        },
    )


if __name__ == "__main__":
    print(train().metrics)
