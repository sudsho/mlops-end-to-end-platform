"""Tests for the feast wrapper.

Imports of feast are heavy and the test only checks our wiring (path
resolution + project listing); no real feast Repo is built here.
"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_list_known_projects_includes_examples() -> None:
    from feature_store.registry import list_known_projects

    names = list_known_projects()
    assert {"churn", "fraud", "recommender"}.issubset(set(names))


def test_repo_path_for_unknown_project_raises() -> None:
    from feature_store.store import get_store

    with pytest.raises(FileNotFoundError):
        get_store("does-not-exist")


def test_default_entity_keys() -> None:
    from serving.render import _default_entity_keys

    assert _default_entity_keys("churn") == ["customer_id"]
    assert _default_entity_keys("fraud") == ["card_id"]
    assert _default_entity_keys("recommender") == ["user_id", "item_id"]
    assert _default_entity_keys("unknown") == ["id"]
