# AI Product Analyst — Deep Agents + A2A (Implementation Plan)

This document specifies a **same-repository application**: three **[Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview)** (LangChain’s harness on LangGraph) that expose **[A2A](https://github.com/google-a2a/A2A)** HTTP services, orchestrated by a **FastAPI backend** and a **small SPA**. The goal is **clarity, real wire-level A2A between processes**, and **minimum operational complexity**—local development first, optional one-command `docker-compose`.

---

## 1. Concept

**Name:** AI Product Analyst Crew (working title)

**Input:** A short product or startup idea (plain text).

**Output:** A single **structured final report** (Markdown or JSON sections: summary, assumptions, risks, recommendations).

**Agents (three):**

| Agent | Role | Style |
|-------|------|--------|
| **Research** | Expand the idea into assumptions, market framing, and context—**without web browsing** (no search tools). | Cheap / local-model friendly; concise. |
| **Critic** | Attack the idea: flaws, risks, edge cases; **skeptical investor** lens. | Does not need to be “nice.” |
| **Synthesizer** | Merge research + critique into one **coherent, structured report** for a human reader. | Final voice; no new wild claims. |

**Implementation rule:** Each agent uses **only** the Deep Agents SDK (`deepagents` + LangGraph runtime). The orchestrator talks to agents **only** via **A2A over HTTP** (separate OS processes, localhost TCP). Do not short-circuit with direct in-process graph calls for the main workflow—this keeps one code path for local dev and future deployment.

---

## 2. A2A, “the network,” and terminology

### 2.1 What “real A2A” means here

- **A2A is an HTTP-based protocol** (agent card, tasks/messages, response envelopes). **Separate processes** each run an A2A-compatible server bound to a port (e.g. `8001`–`8003`).
- **Loopback is still “the network”:** `http://127.0.0.1:PORT` uses the TCP stack. You do **not** need separate VMs, Kubernetes, or cloud hosts for a valid v1. Multi-process + localhost matches production-shaped behavior without distributed-system ceremony.

### 2.2 “Deploy each agent individually”

- **Production:** You may run each agent in its own container or host. **Development:** Running four processes on one machine (three agents + orchestrator API) **is** individual deployment at the process level—good enough for learning and integration tests.

### 2.3 “Sandbox” — do not confuse two meanings

| Term | Meaning |
|------|--------|
| **Dev orchestration** | One command starts all services: `docker-compose` or a process launcher. This is what you want for “run the repo once, everything is live.” |
| **Deep Agents “sandbox”** (docs) | Optional **isolated execution backends** for tools (e.g. shell/code in Modal/Daytona). **Orthogonal** to A2A topology. v1 can omit tool sandboxes; focus on **process isolation** via separate agent servers. |

---

## 3. Why this shape (Deep Agents × A2A × star topology)

- **Deep Agents per role:** Planning, optional filesystem-style context, optional subagents, LangGraph streaming/durability later—see [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview).
- **A2A between orchestrator and each agent:** Each role is a **service** with a stable contract. Clear boundaries, no monolithic graph file, easy to add auth/TLS later.
- **Star topology:** Only the orchestrator sequences the workflow. Agents do not call each other—avoids mesh discovery and cycles.

---

## 4. Collaboration topology

```text
                         ┌──────────────────────┐
                         │  Orchestrator API    │
                         │  FastAPI :8080       │
                         │  (+ optional SPA)    │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │ A2A HTTP client     │                     │
              ▼                     ▼                     ▼
        ┌──────────┐         ┌──────────┐         ┌──────────────┐
        │ Research │         │  Critic  │       │ Synthesizer  │
        │  :8001   │         │  :8002   │       │   :8003      │
        └──────────┘         └──────────┘         └──────────────┘
```

**Orchestrator responsibilities:**

1. Accept user input (HTTP from SPA).
2. **Step 1 — Research (A2A):** send the **user idea** (and any session metadata if added later).
3. **Step 2 — Critic (A2A):** send **idea + research output** (serialized in task payload).
4. **Step 3 — Synthesizer (A2A):** send **idea + research + critique**.
5. Return the **final report** to the client; optionally stream **per-step progress** (SSE).

**Agents:** Expose A2A servers only; **no** peer-to-peer calls in v1.

**Optional later:** Critic requests clarification from Research (mesh). Defer.

---

## 5. Data contracts (step I/O)

Keep payloads **JSON-friendly** and version them with optional `schema_version` if you evolve.

### 5.1 Shared Pydantic models (recommended location: `packages/shared`)

Define in `packages/shared/src/shared/payloads.py` (names illustrative—align with A2A task `message`/`parts` your SDK uses):

**Research**

- **Input:** `{ "idea": "<plain text>" }`
- **Output:** `{ "assumptions": [...], "market_context": "...", "open_questions": [...] }` **or** `{ "content": "<markdown>" }` for minimal v1.

**Critic**

- **Input:** `{ "idea": "...", "research": <object or string> }`
- **Output:** `{ "risks": [...], "flaws": [...], "investor_concerns": [...] }`

**Synthesizer**

- **Input:** `{ "idea": "...", "research": ..., "critique": ... }`
- **Output:** `{ "executive_summary": "...", "sections": { ... } }` **or** `{ "report": "<markdown>" }`

**Orchestrator API (app-owned, not A2A):**

- **Request:** `POST /api/analyze` body: `{ "idea": "..." }`
- **Response (sync):** `{ "report": "...", "steps": { "research": ..., "critic": ..., "synthesizer": ... } }` (shape as needed; keep `report` as the primary UI field).
- **Streaming (optional v1):** `GET` or `POST` with SSE: events like `step_started`, `step_completed`, `final`—see §7.

**Policy:** Enforce “no web” for Research by **not** registering search/browser tools in `create_deep_agent` for that package—**code**, not prompt-only.

---

## 6. Repository layout (implementation target)

Use a **uv workspace** (or equivalent) so one lockfile and editable installs across packages. Repo root name may be `AgentMesh` or similar.

```text
.
├── reference/
│   └── PLAN.md                    # this file
├── README.md                      # install, env, run api + agents + frontend
├── pyproject.toml                 # workspace root; members = packages/* + orchestrator
├── docker-compose.yml             # recommended for one-command dev
├── .env.example                   # ports, model IDs, API keys (no secrets)
│
├── packages/
│   ├── shared/
│   │   ├── pyproject.toml
│   │   └── src/shared/
│   │       ├── __init__.py
│   │       ├── payloads.py        # Pydantic models + JSON helpers
│   │       └── prompts.py       # RESEARCH_SYSTEM, CRITIC_SYSTEM, SYNTH_SYSTEM
│   │
│   ├── agent_research/
│   │   ├── pyproject.toml         # depends: shared, deepagents, a2a-sdk, uvicorn/fastapi per SDK
│   │   └── src/agent_research/
│   │       ├── __init__.py
│   │       ├── deep_agent.py      # create_deep_agent(...), build_run_agent()
│   │       └── server.py          # A2A HTTP app entrypoint; binds HOST:PORT from env
│   │
│   ├── agent_critic/
│   │   └── src/agent_critic/      # same pattern
│   │
│   └── agent_synthesizer/
│       └── src/agent_synthesizer/ # same pattern
│
├── orchestrator/
│   ├── pyproject.toml
│   └── src/orchestrator/
│       ├── __init__.py
│       ├── main.py                # FastAPI app factory; CORS; lifespan (optional)
│       ├── routes_analyze.py      # POST /api/analyze; optional SSE route
│       ├── client.py              # Thin A2A client: call_agent(base_url, payload) -> result
│       ├── workflow.py            # run_star_workflow(idea) -> report + intermediates
│       └── settings.py          # pydantic-settings: RESEARCH_URL, CRITIC_URL, ...
│
└── frontend/
    ├── package.json               # Vite + React or Vue or Svelte (pick one; lock it in README)
    ├── vite.config.ts            # proxy /api to http://127.0.0.1:8080 in dev
    └── src/                       # form: idea textarea; display: step status + final report
```

**Collapse option:** If a single package is preferred, merge `packages/*` into one Python package with subpackages `shared`, `agent_research`, …—same boundaries, flatter tree.

**Thin optional CLI:** A `python -m orchestrator.cli` that calls `workflow.run_star_workflow` is useful for CI/golden tests; not the primary UX.

---

## 7. Orchestrator API (FastAPI) — behavior

### 7.1 Configuration (`orchestrator.settings`)

Load from environment (use `pydantic-settings`):

| Variable | Purpose | Example |
|----------|---------|---------|
| `RESEARCH_A2A_URL` | Base URL for Research A2A server | `http://127.0.0.1:8001` |
| `CRITIC_A2A_URL` | Critic | `http://127.0.0.1:8002` |
| `SYNTHESIZER_A2A_URL` | Synthesizer | `http://127.0.0.1:8003` |
| `CORS_ORIGINS` | SPA dev server origins | `http://localhost:5173` |
| `API_HOST` / `API_PORT` | Orchestrator bind | `0.0.0.0` / `8080` |

No hardcoded URLs in business logic—only defaults in settings for local dev.

### 7.2 Routes

- **`POST /api/analyze`:** Body `{ "idea": string }`. Runs the star workflow; returns JSON with final report and optional step payloads for debugging/UI.
- **`GET /api/health`:** Returns `200` when the API process is up (does not need to verify all agents unless you add aggregated health).
- **`GET /api/health/agents` (optional):** Probe the three A2A URLs (lightweight) for a dashboard “all systems go.”

### 7.3 Streaming (recommended for UX)

Long LLM steps block for minutes. Prefer **Server-Sent Events (SSE)** from FastAPI:

- Either a separate route e.g. `POST /api/analyze/stream` that yields events, **or** extend analyze with `Accept: text/event-stream`—pick one pattern and document it in README.

**Minimum events:** `research_started` / `research_done`, `critic_started` / `critic_done`, `synth_started` / `synth_done`, `complete` (with final report). On failure: `error` with message and optional step name.

### 7.4 Serving the SPA

- **Development:** Vite dev server (port `5173` or similar) with **proxy** to FastAPI—simplest hot reload.
- **Production-style local:** Build SPA to `frontend/dist`; FastAPI serves static files from that directory and `GET /` returns `index.html` (catch-all for client-side routing if used).

---

## 8. Frontend (SPA) — behavior

**Stack:** Vite + **one** SPA framework (React, Vue, or Svelte)—choose once and document in README.

**Screens / components (minimal):**

1. **Input:** Multiline text for the idea; **Submit** triggers `POST /api/analyze` or opens SSE connection for streaming route.
2. **Progress:** Show current step (Research → Critic → Synthesizer) from SSE events or from polling if you skip streaming in v1.
3. **Output:** Render final report (Markdown → HTML with a small safe renderer, e.g. `react-markdown` or equivalent).

**CORS:** FastAPI must allow the Vite origin during development.

---

## 9. Per-agent implementation

### 9.1 Deep Agent (`deep_agent.py`)

- Call `create_deep_agent(...)` with:
  - **Model:** from env per role, e.g. `RESEARCH_MODEL=ollama:llama3.2`, `CRITIC_MODEL=...`, `SYNTHESIZER_MODEL=...` (see Deep Agents [models](https://docs.langchain.com/oss/python/deepagents/models)).
  - **System prompt:** from `shared.prompts`.
  - **Tools:** Minimal—built-in planning/todo only if needed. **No** web search, **no** browser tools for Research.
- Expose `async def run_agent(task_text: str) -> str` (or structured dict) that:
  - Builds the user message from the A2A payload.
  - Invokes the compiled graph/agent per Deep Agents docs (`invoke` / async equivalent).
  - Returns text or JSON string for the A2A response body.

### 9.2 A2A server (`server.py`)

- **One HTTP server process per agent**, binding `HOST:PORT` from env (e.g. `RESEARCH_HOST`, `RESEARCH_PORT`).
- Use the **official A2A Python SDK** for your chosen spec revision.
- **Pin** the SDK version in `pyproject.toml`; upgrade deliberately when the spec changes.
- Handler pipeline:
  1. Parse incoming A2A task/message.
  2. Map body → string/JSON for `run_agent`.
  3. Return success/error in the SDK’s expected envelope.

**Do not** implement the full protocol by hand unless necessary—follow upstream examples.

### 9.3 Orchestrator A2A client (`client.py`)

- Small module: given `base_url`, construct client, send task, parse response, raise on HTTP or application errors.
- Used **only** by `workflow.py`—keeps routes thin and testable.

---

## 10. Deployment and one-command dev

### 10.1 Phase A — manual (no Docker)

Four terminals:

1. Research: `uv run python -m agent_research.server` (or equivalent module path).
2. Critic.
3. Synthesizer.
4. Orchestrator: `uv run uvicorn orchestrator.main:app --host 0.0.0.0 --port 8080`  
   Fifth: `npm run dev` in `frontend/` if using Vite.

### 10.2 Phase B — `docker-compose` (recommended)

Services:

| Service | Role |
|---------|------|
| `research` | Agent server; expose `8001:8001` |
| `critic` | `8002` |
| `synthesizer` | `8003` |
| `api` | FastAPI orchestrator; `8080:8080`; `depends_on` the three with healthchecks |
| `frontend` (optional) | Either build static assets into `api` image or separate nginx—simplest v1: **api image builds SPA** and serves `dist` |

Orchestrator container env: `RESEARCH_A2A_URL=http://research:8001`, etc. (use **service names**, not `127.0.0.1`).

### 10.3 Out of scope for v1

- Kubernetes, service mesh, multi-region.
- mTLS / per-agent auth **until** exposed beyond localhost—then add tokens or mutual TLS.

### 10.4 LLM hosting

- **Local:** Ollama / LM Studio.
- **Cloud:** OpenAI / Anthropic / etc. via `.env`—cost-aware.

---

## 11. Testing strategy

| Layer | What to test |
|-------|----------------|
| **Unit** | `shared.payloads` parsing; `workflow` with **mocked** `client` (no network). |
| **Integration** | With all four processes up (or compose): fixed **canned idea** → golden snapshot of final Markdown **or** assert required headings/JSON keys. |
| **Contract** | Optional: httpx against each agent’s A2A health/sample task using recorded fixtures. |

Run integration in CI only if the environment provides models or mocks; otherwise mark as manual/local.

---

## 12. Security and sandboxing (proportionate)

- **Process isolation:** Three agent processes + API process; Docker adds extra isolation.
- **No browsing:** No search tools on Research; disable or omit shell/`execute` tools in v1 unless you use a **sandbox backend** intentionally.
- **Secrets:** `.env` only; `.env.example` without real keys; never commit secrets.

---

## 13. Milestones (implementation order)

1. **Workspace skeleton:** Root `pyproject.toml`, `packages/shared` with prompts + Pydantic payloads; runnable **Research** `deep_agent` from a script (no HTTP).
2. **Research A2A server:** Pin SDK; manual test with SDK client or `curl` per docs.
3. **Critic + Synthesizer** agents and servers (copy pattern).
4. **`orchestrator.client` + `workflow`:** Star sequence with env-based URLs; unit tests with mocks.
5. **FastAPI:** `POST /api/analyze` + optional SSE; health routes.
6. **Frontend:** Submit idea, show progress, show report.
7. **`docker-compose` + README:** One-command bring-up; document ports and env for compose vs host networking.

**Optional after:** Tight JSON schemas, golden files, stronger models for Critic/Synthesizer only, `GET /api/health/agents`.

---

## 14. Summary table

| Topic | Decision |
|-------|----------|
| Agent runtime | **Deep Agents** (`deepagents` + LangGraph) per role |
| Interop | **A2A over HTTP**, **separate processes**, localhost in dev |
| Topology | **Star**—orchestrator only calls agents |
| Human interface | **FastAPI** + **Vite SPA** (not CLI as primary) |
| One-command dev | **`docker-compose`** (optional: native multi-process script) |
| “Sandbox” | **Compose/launcher** for dev; Deep Agents execution sandbox **optional** later |
| Repo | `packages/shared`, `packages/agent_*`, `orchestrator`, `frontend` |

This document is the **source of truth** for v1 implementation; adjust section numbers if you add ADRs later, but keep contracts and topology stable unless intentionally versioned.
