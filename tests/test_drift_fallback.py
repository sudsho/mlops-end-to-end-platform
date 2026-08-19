"""Tests for the KS / chi-square drift fallback.

These run without Evidently installed and cover the offline drift
codepath used by the smoke.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _ref() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "amount": rng.normal(50, 10, 500),
        "n_tx": rng.poisson(2, 500),
        "merchant_category": rng.choice(["grocery", "online", "atm"], 500),
    })


def test_ks_fallback_no_drift_is_low() -> None:
    from monitoring.drift import _ks_drift_score

    ref = _ref()
    score = _ks_drift_score(ref, ref.copy())
    assert isinstance(score, float)
    assert math.isfinite(score)
    assert score == 0.0


def test_ks_fallback_detects_shift() -> None:
    from monitoring.drift import _ks_drift_score

    ref = _ref()
    rng = np.random.default_rng(1)
    cur = pd.DataFrame({
        "amount": rng.normal(90, 15, 500),  # strong mean shift
        "n_tx": rng.poisson(2, 500),
        "merchant_category": rng.choice(["grocery", "online", "atm"], 500),
    })
    score = _ks_drift_score(ref, cur)
    assert 0.0 < score <= 1.0


def test_current_drift_score_uses_fallback_when_no_evidently() -> None:
    import monitoring.drift as drift

    if drift._evidently_available():
        import pytest

        pytest.skip("evidently installed; fallback path not exercised")

    ref = _ref()
    cur = ref.copy()
    cur["amount"] = cur["amount"] + 40
    score = drift.current_drift_score("churn", reference=ref, current=cur)
    assert 0.0 <= score <= 1.0
