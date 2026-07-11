# LLM Handsoff — Context & Learnings

> **Purpose:** When a new LLM session starts or the model changes, this doc provides full context about the project so the new LLM can operate faster without repeating the same mistakes.

---

## 1. Project Overview

**Meower** is an OSINT intelligence platform built as a single-container web app. It orchestrates existing OSINT CLI tools (`theHarvester`, `sherlock`, `holehe`, `maigret`, `ghunt`, etc.), collects results, builds a relationship graph, and generates LLM-powered intelligence reports.

### Tech Stack (final decisions)

| Component | Choice | Why |
|-----------|--------|-----|
| Backend | FastAPI + Python 3.14 | Async, auto-docs, Pydantic validation |
| Frontend | React + Vite + Tailwind 4 | Modern, fast dev, good DX |
| DB | SQLite via SQLAlchemy async | Single container, no external deps |
| LLM | Fanar API (Qatar) | OpenAI-compatible, no local GPU needed |
| LLM SDK | OpenAI Python SDK | Fanar is fully OpenAI-compatible (`/v1/chat/completions`) |
| Container | Single multi-stage Docker | User pulls & runs one image |
| OSINT Tools | CLI subprocess calls | Tools already installed in $PATH |

### Mistake: OpenAI → Fanar switch
The plan originally used Ollama (local) + OpenAI (cloud). The user explicitly said they want **only Fanar**. The Fanar API is OpenAI-compatible so the OpenAI Python SDK is used with `base_url="https://api.fanar.qa/v1"`. Config was changed from `openai_api_key` + `ollama_url` → `fanar_api_key` + `fanar_base_url` + `fanar_model`.

### Mistake: Static files mount at `/` broke API routes
Originally used `app.mount("/", StaticFiles(...))` which caught ALL routes including `/health` and API endpoints. Fixed by using a **catch-all route** at the end instead:
```python
@app.api_route("/{path_name:path}", methods=["GET"])
async def catch_all(request: Request, path_name: str):
    if path_name.startswith("api/") or path_name.startswith("ws/"):
        raise HTTPException(status_code=404)
    ...
```
**Lesson:** Mount `StaticFiles` at a prefix or use catch-all routes. Never mount at `/` when you have API routes.

### Mistake: Pydantic deprecated `class Config`
Original code used `class Config: env_file = ".env"` which is deprecated in Pydantic V2. Fixed with `model_config = SettingsConfigDict(env_file=".env")`. The deprecation warning showed in test output.

### Mistake: Relative import wrong depth
In `backend/app/api/v1/investigations.py`, used `....schemas.investigation` (4 dots) which goes beyond the package. From `app/api/v1/`, you need 3 dots to reach `app/`. Fixed to `...schemas.investigation`.

### Mistake: pytest trio backend errors
Tests were collected twice (once for asyncio, once for trio) and trio tests failed with "no running event loop". Fixed by adding `conftest.py` with `anyio_backend` fixture returning `"asyncio"`.

### Mistake: SQLite "unable to open database file"
Config defaulted to `sqlite+aiosqlite:///./data/meower.db` but `data/` directory didn't exist. Tests failed with `OperationalError`. Fixed by creating `backend/data/` directory.

### Mistake: Async methods not awaited
`LLMService._call` was `async def` but `generate_report` called it without `await`. The test got a coroutine object instead of a string. Fixed by making `generate_report`/`generate_summary` async and using `await`.

### Mistake: Test for `test_llm_service_available` used wrong assertion
Used `assert "Mock report content" in result` but `generate_report` returned a coroutine. After fixing to async/await, the test worked by using `AsyncMock` for `_call`.

---

## 2. Architecture Decisions

### Directory Layout
```
meower/
├── Dockerfile              # Multi-stage: node build frontend → python serve
├── docker-compose.yml      # meower service + optional ollama (profiles)
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Route handlers
│   │   ├── core/           # Config, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── tools/          # Tool adapters (BaseTool + each tool)
│   │   ├── llm/            # Fanar LLM service
│   │   ├── orchestration/  # Pipeline + dispatcher
│   │   ├── graph/          # Relationship graph builder
│   │   └── db/             # Session, base
│   ├── tests/
│   └── requirements.txt
└── frontend/
    └── src/
```

### Tool Adapter Pattern
Each tool implements `BaseTool` with:
```python
class BaseTool(ABC):
    name: str
    category: ToolCategory
    description: str
    async def run(self, target: str, **kwargs) -> ToolResult
```
`ToolResult` contains:
- `tool_name`, `category`, `status` ("success"|"partial"|"error")
- `raw_data` (full CLI output or API response)
- `normalized` (parsed, structured list of findings)
- `error`, `duration_ms`

**Tool Adapter Naming:** `backend/app/tools/<tool_name>.py`, class `XxxTool`.

### Fanar LLM
- Base URL: `https://api.fanar.qa/v1`
- Auth: Bearer token in `Authorization` header
- Uses OpenAI Python SDK with custom `base_url`
- Default model: `Fanar-C-2-27B`
- Key set via `FANAR_API_KEY` env var
- No key → LLM endpoints return 400 with clear message
- Rate limit: 50 req/min for most models

### Investigation Flow
1. User enters seed (email/username/domain) → `POST /api/v1/investigations`
2. API creates `Investigation` record (status: "pending")
3. Frontend polls via WebSocket or GET endpoint
4. Orchestrator builds execution DAG based on seed type
5. Tools run in parallel where dependencies allow
6. Results merged → graph built → LLM report generated
7. Investigation marked "completed"

---

## 3. Environment Variables

```bash
# From backend/.env
DATABASE_URL=sqlite+aiosqlite:///./data/meower.db
SECRET_KEY=dev-secret-key-change-in-prod
LOG_LEVEL=INFO
FANAR_API_KEY=                  # Required for LLM features
FANAR_BASE_URL=https://api.fanar.qa/v1
FANAR_MODEL=Fanar-C-2-27B
CORS_ORIGINS=["*"]
FRONTEND_DIR=                   # Auto-detected, can override
```

## 4. Run Commands

```bash
# Development (2 terminals)
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# Production (single container)
docker build -t meower .
docker run -e FANAR_API_KEY=$KEY -p 8000:8000 meower

# Tests
cd backend && python3 -m pytest tests/ -v

# Check tools
cd backend && python3 scripts/check_tools.py
```

## 5. Key Gotchas

1. **SQLite path:** The `data/` directory must exist relative to where `uvicorn` runs. Default is `./data/meower.db`.
2. **Frontend proxy:** In dev mode, Vite proxies `/api/*` to `localhost:8000`. The catch-all route in `main.py` serves frontend for non-API paths.
3. **Tool CLI dependencies:** Tool adapters assume the CLI binaries are in `$PATH`. The Dockerfile or user must install them.
4. **Fanar API key:** Without this, `/api/v1/reports/generate/*` returns 400. The `/api/v1/reports/status` endpoint shows availability.
5. **Test isolation:** Tests create/drop tables via the fixture in `conftest.py`. The DB file must exist at the configured path.
6. **Async everything:** All subprocess calls in tool adapters MUST use `asyncio.create_subprocess_exec`, not `subprocess.run`.

## 6. What's Built vs What's Planned

### ✅ Built (Phase 1 & partial Phase 2)
- [x] FastAPI skeleton with all route handlers
- [x] SQLAlchemy models + async session
- [x] React frontend (Dashboard, New Investigation, Detail)
- [x] Fanar LLM service with report generation
- [x] Tool adapter base class + registry
- [x] Docker multi-stage build
- [x] GitHub Actions CI
- [x] 12 passing tests

### 🚧 In Progress (Phase 2)
- [ ] Tool adapters for each OSINT tool
- [ ] Orchestrator pipeline (DAG execution)
- [ ] Graph builder
- [ ] Integration tests for tool outputs

### 📅 Planned (Phases 3-7)
- [ ] WebSocket streaming for real-time progress
- [ ] Person graph + relationship tree
- [ ] LLM prompt templates refinement
- [ ] PDF/JSON export
- [ ] Auth (JWT)
- [ ] Celery for heavy investigations

## 7. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| Phase 1 | SQLite instead of PostgreSQL | Single container, no external DB needed |
| Phase 1 | Async SQLAlchemy + aiosqlite | Non-blocking, works with FastAPI lifespan |
| Phase 1 | Catch-all route instead of StaticFiles mount | API routes must take priority over frontend |
| Phase 1 | Fanar instead of OpenAI/Ollama | User's explicit choice |
| Phase 1 | OpenAI SDK with custom base_url for Fanar | Fanar is OpenAI-compatible, no extra SDK needed |
| Phase 2 | CLI subprocess per tool adapter | Tools already installed; no need to reimplement |
| Phase 2 | `normalized` field in ToolResult | Separates raw CLI output from structured data |

---

*Last updated: 2026-07-11*
