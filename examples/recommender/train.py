"""Recommender training. Binary click-through model (logreg)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class Result:
    model: Any
    metrics: dict[str, float]


FEATURES = ["user_clicks_30d", "user_engagement_30d", "item_popularity_24h", "content_match"]


def _ndcg_at_k(y_true: pd.Series, y_score: np.ndarray, group: pd.Series, k: int = 10) -> float:
    df = pd.DataFrame({"y": y_true.values, "s": y_score, "g": group.values})
    out = []
    for _, sub in df.groupby("g"):
        sub = sub.sort_values("s", ascending=False).head(k)
        gains = sub["y"].values
        idx = np.arange(1, len(gains) + 1)
        dcg = (gains / np.log2(idx + 1)).sum()
        ideal = (np.sort(gains)[::-1] / np.log2(idx + 1)).sum()
        out.append(0.0 if ideal == 0 else dcg / ideal)
    return float(np.mean(out)) if out else 0.0


def train(data_path: str | None = None) -> Result:
    if data_path and Path(data_path).exists():
        df = pd.read_parquet(data_path)
    else:
        from examples._data.make_synthetic import recommender
        df = recommender(n=6000)

    y = df["clicked"].astype(int)
    X = df[FEATURES]

    Xtr, Xte, ytr, yte, gtr, gte = train_test_split(
        X, y, df["user_id"], test_size=0.2, random_state=11
    )
    pipe = Pipeline([
        ("sc", StandardScaler()),
        ("clf", LogisticRegression(max_iter=500)),
    ])
    pipe.fit(Xtr, ytr)
    proba = pipe.predict_proba(Xte)[:, 1]

    return Result(
        model=pipe,
        metrics={
            "roc_auc": float(roc_auc_score(yte, proba)),
            "ndcg_10": _ndcg_at_k(yte, proba, gte, k=10),
            "n_train": float(len(Xtr)),
        },
    )


if __name__ == "__main__":
    print(train().metrics)
