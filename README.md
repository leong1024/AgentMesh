# AgentMesh

**AgentMesh** is a multi-agent **product and startup idea analyzer**. You submit a short idea in natural language; the system runs a **research** pass (assumptions and market framing), a **skeptical critique** pass (risks and investor concerns), then **merges** both into a single structured report with an executive summary and Markdown body. The UI streams progress and renders the final report.

The design goal is a **clear, inspectable pipeline**: worker agents speak the **Agent-to-Agent (A2A)** protocol over HTTP as separate processes; the **orchestrator** coordinates them and produces the final narrative in one place.

For deeper architecture notes, see [reference/PLAN.md](reference/PLAN.md).

---

## What it does

| Stage | Role |
|-------|------|
| **Research** | Expands the idea into assumptions, market context, and open questions (general knowledge only; no web browsing in the default setup). |
| **Critic** | Challenges the idea from an early-stage investor perspective: flaws, risks, and concerns. |
| **Orchestrator** | Calls Research and Critic in sequence over A2A, then runs an **in-process Deep Agent** to synthesize a coherent JSON + Markdown report from their outputs. |

The **FastAPI** backend exposes JSON and **Server-Sent Events (SSE)** endpoints; the **React** SPA submits ideas and displays step progress and the synthesized report.

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| **Language & tooling** | Python 3.11+, [uv](https://docs.astral.sh/uv/) (workspace), [Ruff](https://docs.astral.sh/ruff/) |
| **Worker agents** | [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) (LangGraph), [LangChain](https://python.langchain.com/) with **Google Gen AI** chat models (`google_genai:…` model ids) |
| **Inter-service protocol** | [A2A](https://github.com/google-a2a/A2A) JSON-RPC over HTTP ([a2a-sdk](https://pypi.org/project/a2a-sdk/)), separate Uvicorn processes per agent |
| **Orchestrator API** | [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [httpx](https://www.python-httpx.org/) (A2A client), [sse-starlette](https://github.com/sysid/sse-starlette) for streaming |
| **Data contracts** | [Pydantic](https://docs.pydantic.dev/) v2 payloads in `packages/shared` |
| **Frontend** | [Vite](https://vitejs.dev/), [React](https://react.dev/) 19, [TypeScript](https://www.typescriptlang.org/), [Vitest](https://vitest.dev/), [react-markdown](https://github.com/remarkjs/react-markdown) + [remark-gfm](https://github.com/remarkjs/remark-gfm) for report rendering |
| **Deployment (optional)** | [Docker Compose](https://docs.docker.com/compose/) — builds the SPA into the API image and runs Research, Critic, and the orchestrator |

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ (for the frontend)
- A [Google AI Studio](https://aistudio.google.com/apikey) or Google Cloud API key: set **`GEMINI_API_KEY`** or **`GOOGLE_API_KEY`** (LangChain’s Google integration prefers `GOOGLE_API_KEY`; if only `GEMINI_API_KEY` is set, it is copied at runtime). Configure model ids in `.env` (see `.env.example`).

---

## Quick start (local, no Docker)

1. **Install dependencies**

   ```bash
   uv sync --all-packages --group dev
   ```

   Use `--all-packages` so every workspace member (agents, orchestrator, shared) is installed.

   ```bash
   cd frontend && npm install && cd ..
   ```

2. **Environment**

   Copy `.env.example` to `.env` (for example `copy .env.example .env` on Windows, or `cp .env.example .env` on Linux/macOS).

   Edit `.env`: set **`GEMINI_API_KEY`** (or **`GOOGLE_API_KEY`**), and adjust **`RESEARCH_MODEL`**, **`CRITIC_MODEL`**, and **`ORCHESTRATOR_MODEL`** if needed (each id must start with `google_genai:`). Processes load `.env` via `python-dotenv`.

3. **Run services** (three terminals from the repo root)

   ```bash
   uv run python -m uvicorn agent_research.server:create_app --factory --host 0.0.0.0 --port 8001
   ```

   ```bash
   uv run python -m uvicorn agent_critic.server:create_app --factory --host 0.0.0.0 --port 8002
   ```

   ```bash
   uv run uvicorn orchestrator.main:create_app --factory --host 0.0.0.0 --port 8080
   ```

4. **Start the UI**

   ```bash
   cd frontend && npm run dev
   ```

   Open the printed URL (for example `http://localhost:5173`). The dev server proxies `/api` to the orchestrator with long timeouts and SSE-friendly headers.

   If streamed steps or the report appear only after the full run completes, set in `frontend/.env`:

   ```text
   VITE_ORCHESTRATOR_URL=http://127.0.0.1:8080
   ```

   so the browser calls the orchestrator directly for the analyze stream (avoids some dev-proxy buffering).

### Optional: serve the built UI from the API

```bash
cd frontend && npm run build && cd ..
set STATIC_DIR=frontend\dist
uv run uvicorn orchestrator.main:create_app --factory --host 0.0.0.0 --port 8080
```

Then open `http://127.0.0.1:8080`.

---

## Docker Compose

Builds the frontend into the image and runs two A2A workers (Research, Critic) plus the API.

```bash
docker compose up --build
```

- **API + bundled SPA:** `http://localhost:8080`
- **A2A workers:** ports `8001` and `8002` (exposed for debugging)

Compose reads the project `.env` for substitution. Set **`GEMINI_API_KEY`** (and optionally **`GOOGLE_API_KEY`**) so containers can call the Google Gen AI API.

---

## CLI (headless)

With agents and environment configured:

```bash
uv run agentmesh analyze --idea "My startup idea..."
```

JSON output:

```bash
uv run agentmesh analyze --idea "..." --json
```

---

## Tests

**Python** (workspace root):

```bash
uv run pytest packages/shared/tests orchestrator/tests packages/agent_research/tests -q
```

Optional LLM smoke tests (requires `GEMINI_API_KEY` or `GOOGLE_API_KEY`, valid `*_MODEL`, and `RUN_LLM_TESTS=1`):

```bash
set RUN_LLM_TESTS=1
uv run pytest packages/agent_research/tests/test_deep_agent_llm.py -q
```

**Frontend:**

```bash
cd frontend && npm test
```

### CI markers

- `integration` — broader tests (see `pyproject.toml`).
- `requires_llm` — needs a real model; not run in default CI.

---

## Lint (Python)

```bash
uv run ruff check packages orchestrator
uv run ruff format packages orchestrator
```

---

## Repository layout

| Path | Contents |
|------|-----------|
| `packages/shared` | Shared Pydantic payloads, prompts, A2A app helpers |
| `packages/agent_research`, `packages/agent_critic` | Deep Agent + A2A server per role |
| `packages/agent_synthesizer` | Optional standalone package (not used by the default orchestrator path) |
| `orchestrator` | FastAPI app, A2A HTTP client, orchestrator Deep Agent synthesis, SSE streaming |
| `frontend` | Vite + React SPA |
| `reference/` | Architecture notes and planning documents |
