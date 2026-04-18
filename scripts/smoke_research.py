"""Optional smoke: run Research deep agent (requires Ollama or configured model)."""

from __future__ import annotations

import asyncio
import os
import sys


async def main() -> None:
    if os.environ.get("RUN_LLM_TESTS") != "1":
        print("Set RUN_LLM_TESTS=1 to run this script.", file=sys.stderr)
        sys.exit(0)
    from agent_research.deep_agent import run_research

    out = await run_research('{"idea":"A habit tracker for remote teams."}')
    print(out)


if __name__ == "__main__":
    asyncio.run(main())
