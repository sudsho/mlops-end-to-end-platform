"""Generate small synthetic datasets for the example projects.

Run from repo root:  python examples/_data/make_synthetic.py
Outputs go to examples/<project>/data/{train,reference,current}.parquet
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RNG = np.random.default_rng(7)


def churn(n: int = 5000) -> pd.DataFrame:
    df = pd.DataFrame({
        "customer_id": [f"c{i:06d}" for i in range(n)],
        "tenure_months": RNG.integers(0, 73, n),
        "monthly_charges": RNG.uniform(15, 120, n).round(2),
        "total_charges": RNG.uniform(0, 8000, n).round(2),
        "contract_type": RNG.choice(["mtm", "1yr", "2yr"], n),
        "internet_service": RNG.choice(["fiber", "dsl", "none"], n),
        "payment_method": RNG.choice(["card", "check", "transfer"], n),
        "num_support_calls_30d": RNG.poisson(0.6, n),
        "num_late_payments_90d": RNG.poisson(0.3, n),
        "auto_pay": RNG.integers(0, 2, n),
        "paperless_billing": RNG.integers(0, 2, n),
    })
    score = (
        -1.5
        + 0.04 * (60 - df["tenure_months"])
        + 0.005 * (df["monthly_charges"] - 50)
        + 0.6 * (df["num_support_calls_30d"] >= 2).astype(int)
        + 0.5 * (df["contract_type"] == "mtm").astype(int)
    )
    p = 1 / (1 + np.exp(-score))
    df["churned"] = (RNG.uniform(size=n) < p).astype(int)
    df["event_ts"] = pd.Timestamp.utcnow() - pd.to_timedelta(RNG.integers(0, 30, n), unit="D")
    return df


def fraud(n: int = 8000, drift: bool = False) -> pd.DataFrame:
    base_amount_mean = 80 if not drift else 130
    df = pd.DataFrame({
        "card_id": [f"k{i % 4000:06d}" for i in range(n)],
        "merchant_id": [f"m{i % 800:05d}" for i in range(n)],
        "amount": RNG.gamma(2.0, base_amount_mean / 2, n).round(2),
        "amount_zscore_1h": RNG.normal(0, 1, n).round(3),
        "num_tx_1h": RNG.poisson(2.5, n),
        "num_unique_merchants_1h": RNG.poisson(1.5, n),
        "time_since_last_tx_s": RNG.integers(1, 86400, n),
        "card_present": RNG.integers(0, 2, n),
        "cross_border": RNG.integers(0, 2, n),
        "merchant_category": RNG.choice(["grocery", "online", "atm", "travel"], n),
    })
    score = (
        -3.0
        + 0.01 * df["amount"]
        + 0.4 * df["cross_border"]
        + 0.6 * (df["merchant_category"] == "atm").astype(int)
        - 0.05 * df["card_present"]
    )
    p = 1 / (1 + np.exp(-score))
    df["is_fraud"] = (RNG.uniform(size=n) < p).astype(int)
    df["event_ts"] = pd.Timestamp.utcnow() - pd.to_timedelta(RNG.integers(0, 7, n), unit="D")
    return df


def recommender(n: int = 6000) -> pd.DataFrame:
    df = pd.DataFrame({
        "user_id": [f"u{i % 1500:06d}" for i in range(n)],
        "item_id": [f"i{i % 800:05d}" for i in range(n)],
        "user_clicks_30d": RNG.poisson(15, n),
        "user_engagement_30d": RNG.uniform(0, 1, n).round(3),
        "item_popularity_24h": RNG.uniform(0, 1, n).round(3),
        "content_match": RNG.uniform(0, 1, n).round(3),
    })
    score = -1.0 + 1.5 * df["item_popularity_24h"] + 1.2 * df["content_match"]
    p = 1 / (1 + np.exp(-score))
    df["clicked"] = (RNG.uniform(size=n) < p).astype(int)
    df["event_ts"] = pd.Timestamp.utcnow() - pd.to_timedelta(RNG.integers(0, 7, n), unit="D")
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["parquet", "csv"], default="csv")
    args = ap.parse_args()
    write = (lambda df, p: df.to_parquet(p, index=False)) if args.format == "parquet" \
            else (lambda df, p: df.to_csv(str(p).replace(".parquet", ".csv"), index=False))

    for name, builder in (("churn", churn), ("fraud", fraud), ("recommender", recommender)):
        d = ROOT / "examples" / name / "data"
        d.mkdir(parents=True, exist_ok=True)
        write(builder(), d / "train.parquet")
        write(builder(), d / "reference.parquet")
        if name == "fraud":
            write(builder(drift=True), d / "current.parquet")
        else:
            write(builder(), d / "current.parquet")
        print(f"wrote {name} data -> {d}")


if __name__ == "__main__":
    main()
