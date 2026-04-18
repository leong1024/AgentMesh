"""Product analysis workflow: A2A Research + Critic, then orchestrator Deep Agent synthesis."""

from __future__ import annotations

from orchestrator.deep_workflow import (
    run_analyze_workflow,
    run_analyze_workflow_stream,
)

# Backwards-compatible names for routes and CLI
run_star_workflow = run_analyze_workflow
run_star_workflow_stream = run_analyze_workflow_stream
