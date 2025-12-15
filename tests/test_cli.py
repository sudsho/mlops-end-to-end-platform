"""Smoke tests for the click cli."""
from __future__ import annotations

import json

from click.testing import CliRunner

from cli.main import cli


def test_cli_help() -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["--help"])
    assert res.exit_code == 0
    assert "project" in res.output
    assert "train" in res.output


def test_cli_status_lists_projects(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["status"])
    assert res.exit_code == 0
    rows = json.loads(res.output)
    names = {r["name"] for r in rows}
    assert {"churn", "fraud", "recommender"}.issubset(names)


def test_cli_project_new_creates_files(tmp_path, monkeypatch) -> None:
    """cmd_project_new creates examples/<name>/ with the expected files."""
    from cli import commands

    monkeypatch.setattr(commands, "ROOT", tmp_path)

    out = commands.cmd_project_new("anomalies")
    assert out["ok"]
    assert (tmp_path / "examples" / "anomalies" / "README.md").exists()
    assert (tmp_path / "examples" / "anomalies" / "feature_definitions.py").exists()
    assert (tmp_path / "examples" / "anomalies" / "train.py").exists()

    out2 = commands.cmd_project_new("anomalies")
    assert not out2["ok"]
