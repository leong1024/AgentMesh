# AgentMesh

AI Product Analyst crew: three **[Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview)** (Research, Critic, Synthesizer) exposed as **[A2A](https://github.com/google-a2a/A2A)** JSON-RPC services, orchestrated in a **star topology** by a **FastAPI** app with a **Vite + React** UI.

See [reference/PLAN.md](reference/PLAN.md) for architecture and terminology.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ (for the frontend)
- A **[Groq](https://console.groq.com/)** API key (`GROQ_API_KEY`). All three agents call Groq over HTTPS via LangChain (`langchain-groq`); model ids use the unified `groq:...` form (see `.env.example`).

## Quick start (local, no Docker)

1. Install dependencies:

   ```bash
   uv sync --all-packages --group dev
   ```

   Always include `--all-packages` so every workspace member (agents, orchestrator, shared) is installed.

   ```bash
   cd frontend && npm install && cd ..
   ```

2. Copy environment template:

   ```bash
   copy .env.example .env
   ```

   Edit `.env`: set **`GROQ_API_KEY`**, and adjust `*_MODEL` if you want a different Groq model (each must start with `groq:`).

3. In **four** terminals from the repo root:

   ```bash
   uv run python -m uvicorn agent_research.server:create_app --factory --host 0.0.0.0 --port 8001
   ```

   ```bash
   uv run python -m uvicorn agent_critic.server:create_app --factory --host 0.0.0.0 --port 8002
   ```

   ```bash
   uv run python -m uvicorn agent_synthesizer.server:create_app --factory --host 0.0.0.0 --port 8003
   ```

   ```bash
   uv run uvicorn orchestrator.main:create_app --factory --host 0.0.0.0 --port 8080
   ```

4. Start the UI (dev server proxies `/api` to the orchestrator):

   ```bash
   cd frontend && npm run dev
   ```

   Open the printed URL (e.g. http://localhost:5173).

### Optional: serve the built UI from the API

```bash
cd frontend && npm run build && cd ..
set STATIC_DIR=frontend\dist
uv run uvicorn orchestrator.main:create_app --factory --host 0.0.0.0 --port 8080
```

Then open http://127.0.0.1:8080

## Docker Compose

Builds the frontend into the image and runs three agents plus the API.

```bash
docker compose up --build
```

- API + bundled SPA: http://localhost:8080  
- Agents: ports `8001`–`8003` (mapped for debugging).

Compose reads a project `.env` for variable substitution. Set **`GROQ_API_KEY`** there (or in your shell) so agent containers can reach the Groq API.

## CLI (headless)

With agents and env configured:

```bash
uv run agentmesh analyze --idea "My startup idea..."
```

JSON output:

```bash
uv run agentmesh analyze --idea "..." --json
```

## Tests

Python (workspace root):

```bash
uv run pytest packages/shared/tests orchestrator/tests packages/agent_research/tests -q
```

Optional LLM smoke (needs `GROQ_API_KEY`, valid `*_MODEL`, and `RUN_LLM_TESTS=1`):

```bash
set RUN_LLM_TESTS=1
uv run pytest packages/agent_research/tests/test_deep_agent_llm.py -q
```

Frontend:

```bash
cd frontend && npm test
```

## CI markers

- `integration` — broader tests (see `pyproject.toml`).
- `requires_llm` — needs a real model; not run in default CI.

## Lint (Python)

```bash
uv run ruff check packages orchestrator
uv run ruff format packages orchestrator
```

## Repository layout

- `packages/shared` — Pydantic payloads, prompts, A2A helpers.
- `packages/agent_*` — Deep Agent + A2A server per role.
- `orchestrator` — FastAPI, A2A client, star workflow, SSE stream.
- `frontend` — Vite React UI.
