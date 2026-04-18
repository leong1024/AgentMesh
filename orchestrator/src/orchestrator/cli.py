"""Typer CLI for headless analysis (CI / golden tests)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import typer
from shared.env_load import load_local_env

from orchestrator.a2a_client import HttpA2AClient
from orchestrator.settings import Settings
from orchestrator.workflow import run_star_workflow

app = typer.Typer(no_args_is_help=True)


@app.command()
def analyze(
    idea: str | None = typer.Option(None, "--idea", "-i", help="Idea text"),
    idea_file: Path | None = typer.Option(
        None,
        "--idea-file",
        "-f",
        help="Read idea from file (UTF-8)",
    ),
    json_out: bool = typer.Option(False, "--json", help="Print JSON instead of report"),
) -> None:
    """Run the star workflow and print the final report (or full JSON)."""
    load_local_env()
    text = idea
    if idea_file is not None:
        text = idea_file.read_text(encoding="utf-8")
    if not text or not text.strip():
        raise typer.BadParameter("Provide --idea or --idea-file with non-empty content")

    async def _run() -> None:
        settings = Settings()
        client = HttpA2AClient(httpx.Timeout(settings.http_timeout_seconds))
        result = await run_star_workflow(text.strip(), client, settings)
        if json_out:
            print(json.dumps(result.model_dump(), indent=2))
        else:
            print(result.report)

    asyncio.run(_run())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
