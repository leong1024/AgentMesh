"""Typer CLI for headless analysis via Orchestrator public API."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import typer
from shared.env_load import load_local_env

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
    """Run analysis and print the final report (or full JSON)."""
    load_local_env()
    text = idea
    if idea_file is not None:
        text = idea_file.read_text(encoding="utf-8")
    if not text or not text.strip():
        raise typer.BadParameter("Provide --idea or --idea-file with non-empty content")

    api_url = os.environ.get("ORCHESTRATOR_API_URL", "http://127.0.0.1:8080").rstrip("/")
    timeout_s = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "600"))
    with httpx.Client(timeout=httpx.Timeout(timeout_s)) as client:
        resp = client.post(f"{api_url}/api/analyze", json={"idea": text.strip()})
    resp.raise_for_status()
    payload = resp.json()
    if json_out:
        print(json.dumps(payload, indent=2))
    else:
        print(payload.get("report", ""))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
