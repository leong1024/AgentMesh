# AgentMesh

AI Product Analyst crew: three **[Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview)** (Research, Critic, Synthesizer) exposed as **[A2A](https://github.com/google-a2a/A2A)** JSON-RPC services, orchestrated in a **star topology** by a **FastAPI** app with a **Vite + React** UI.

See [reference/PLAN.md](reference/PLAN.md) for architecture and terminology.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ (for the frontend)
- A local LLM via **Ollama** (default in `.env.example`), or **Groq** / other providers via LangChain model strings (see below).

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

   Edit `.env` if ports or models differ.

3. Configure models and keys in `.env`:

   - **Ollama (default):** start Ollama locally; keep `*_MODEL=ollama:...`.
   - **Groq:** set `GROQ_API_KEY` and use unified model strings, for example:

     ```text
     RESEARCH_MODEL=groq:llama-3.1-70b-versatile
     CRITIC_MODEL=groq:llama-3.1-70b-versatile
     SYNTHESIZER_MODEL=groq:llama-3.1-70b-versatile
     ```

     The repo resolves `groq:` prefixes with `langchain.chat_models.init_chat_model` and passes a chat model into `create_deep_agent`, matching the pattern from the [LangChain](https://python.langchain.com/) / Groq docs.

4. Start **Ollama** if you use `ollama:...` models (skip if you only use Groq).

4. In **four** terminals from the repo root:

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

5. Start the UI (dev server proxies `/api` to the orchestrator):

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

Containers expect the LLM to be reachable from **inside** the container. For Ollama on the host, you typically need extra networking (e.g. `extra_hosts` / `host.docker.internal`) or run Ollama in the same compose stack—adjust for your OS and security requirements.

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

Optional LLM smoke (needs a running model and `RUN_LLM_TESTS=1`):

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
