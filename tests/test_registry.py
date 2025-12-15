"""Promotion policy tests with mocked mlflow client."""
from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import pytest


def _fake_run(metrics: dict[str, float]) -> SimpleNamespace:
    return SimpleNamespace(data=SimpleNamespace(metrics=metrics))


def _fake_version(version: str = "1") -> SimpleNamespace:
    return SimpleNamespace(version=version, run_id="r1", current_stage="None",
                           creation_timestamp="0")


def test_promote_passes_when_metric_above_threshold() -> None:
    from registry import policy

    fake = mock.MagicMock()
    fake.get_run.return_value = _fake_run({"roc_auc": 0.85})
    fake.search_model_versions.return_value = [_fake_version()]

    with mock.patch.object(policy, "_client", return_value=fake):
        ok = policy.promote_if_passes("churn", run_id="r1", threshold=0.7)
        assert ok is True
        fake.transition_model_version_stage.assert_called_once()


def test_promote_skips_when_metric_below_threshold() -> None:
    from registry import policy

    fake = mock.MagicMock()
    fake.get_run.return_value = _fake_run({"roc_auc": 0.55})

    with mock.patch.object(policy, "_client", return_value=fake):
        ok = policy.promote_if_passes("fraud", run_id="r1", threshold=0.7)
        assert ok is False
        fake.transition_model_version_stage.assert_not_called()


def test_promote_skips_when_metric_missing() -> None:
    from registry import policy

    fake = mock.MagicMock()
    fake.get_run.return_value = _fake_run({})

    with mock.patch.object(policy, "_client", return_value=fake):
        ok = policy.promote_if_passes("recommender", run_id="r1")
        assert ok is False
