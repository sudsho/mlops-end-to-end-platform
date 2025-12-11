"""mlops cli: lifecycle management for projects on the platform."""
from __future__ import annotations

import json
import sys

import click

from config import load_config

from . import commands as cmd


@click.group()
@click.option("--config", "config_path", default=None, help="Path to platform.yaml")
@click.pass_context
def cli(ctx: click.Context, config_path: str | None) -> None:
    """Manage ML projects on the platform."""
    ctx.ensure_object(dict)
    ctx.obj["cfg"] = load_config(config_path)


@cli.group()
def project() -> None:
    """Project lifecycle commands."""


@project.command("new")
@click.option("--name", required=True)
def project_new(name: str) -> None:
    out = cmd.cmd_project_new(name)
    click.echo(json.dumps(out, indent=2))


@cli.command()
@click.option("--project", "project_name", required=True)
def train(project_name: str) -> None:
    out = cmd.cmd_train(project_name)
    click.echo(json.dumps(out, indent=2, default=str))


@cli.command()
@click.option("--project", "project_name", required=True)
@click.option("--run-id", default=None)
@click.option("--metric", default="roc_auc")
@click.option("--threshold", type=float, default=0.7)
def register(project_name: str, run_id: str | None, metric: str, threshold: float) -> None:
    out = cmd.cmd_register(project_name, run_id, metric, threshold)
    click.echo(json.dumps(out, indent=2))


@cli.command()
@click.option("--project", "project_name", required=True)
@click.option("--target", default="staging")
def deploy(project_name: str, target: str) -> None:
    out = cmd.cmd_deploy(project_name, target)
    click.echo(json.dumps(out, indent=2))


@cli.command()
def status() -> None:
    cfg = load_config()
    rows = []
    for p in cfg.projects:
        rows.append({"name": p.name, "objective": p.objective, "fv": p.feature_view})
    click.echo(json.dumps(rows, indent=2))


@cli.command()
@click.option("--project", "project_name", required=True)
def drift(project_name: str) -> None:
    out = cmd.cmd_drift(project_name)
    click.echo(json.dumps(out, indent=2))


def main() -> int:
    cli(obj={})
    return 0


if __name__ == "__main__":
    sys.exit(main())
