"""Drift detector smoke tests.

Builds two small dataframes (one a perturbation of the other) and
calls evidently. We only assert the function returns a finite float
in [0, 1] - exact values move with evidently versions.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def reference() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "amount": rng.normal(50, 10, 500),
        "n_tx": rng.poisson(2, 500),
        "merchant_category": rng.choice(["grocery", "online", "atm"], 500),
    })


@pytest.fixture
def shifted(reference: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    return pd.DataFrame({
        "amount": rng.normal(80, 15, 500),  # mean shift
        "n_tx": rng.poisson(2, 500),
        "merchant_category": rng.choice(["grocery", "online", "atm"], 500),
    })


def test_drift_score_returns_finite_float(reference, shifted) -> None:
    pytest.importorskip("evidently")
    from monitoring.drift import current_drift_score

    score = current_drift_score("churn", reference=reference, current=shifted)
    assert isinstance(score, float)
    assert math.isfinite(score)
    assert 0.0 <= score <= 1.0
