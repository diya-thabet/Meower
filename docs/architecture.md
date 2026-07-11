# Meower Architecture

## Overview

Meower is a single-container web application that orchestrates existing OSINT CLI tools, correlates their output into a relationship graph, and generates intelligence reports using the Fanar LLM API.

```
User (Browser)
     │
     ▼
┌─────────────────────┐
│   React Frontend     │   Port 5173 (dev) / served by FastAPI (prod)
│   Vite + Tailwind   │
│   Cytoscape.js      │
└─────────┬───────────┘
          │ HTTP / WS
          ▼
┌─────────────────────────────────────────────────────┐
│                 FastAPI Backend                      │  Port 8000
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  API Layer   │  │  Auth/AuthZ  │  │  WS Stream │  │
│  │  (api/v1/)   │  │  (core/)     │  │  (active)  │  │
│  └──────┬───────┘  └──────────────┘  └──────┬─────┘  │
│         │                                    │       │
│  ┌──────▼─────────────────────┐  ┌───────────▼────┐  │
│  │   Orchestration Layer      │  │  WS Manager     │  │
│  │  (orchestration/)          │  │  (ws/manager)   │  │
│  │  Pipeline → Dispatcher →  │  │  Broadcast by   │  │
│  │  Runner                    │  │  investigation  │  │
│  └──────┬──────────┬─────────┘  └─────────────────┘  │
│         │          │                                   │
│  ┌──────▼──┐ ┌────▼──┐ ┌────▼──┐ ┌────▼──┐        │
│  │  Email   │ │Username│ │ Social │ │ Domain │        │
│  │  Tools   │ │ Tools  │ │ Tools  │ │ Tools  │        │
│  │  (5)     │ │ (3)    │ │ (3)    │ │ (4)    │        │
│  └─────────┘ └────────┘ └────────┘ └────────┘        │
│         │                                             │
│  ┌──────▼──────────┐  ┌───────────────┐            │
│  │  Graph Builder   │  │  LLM Service  │            │
│  │  (graph/)        │  │  (Fanar)      │            │
│  │  Entity extract  │  │  Report gen   │            │
│  │  Node/edge JSON  │  │  Summaries    │            │
│  └──────┬──────────┘  └──────┬────────┘            │
│         │                    │                       │
│  ┌──────▼────────────────────▼──────────────────┐  │
│  │           Data Layer                          │  │
│  │  SQLAlchemy (async) + SQLite                 │  │
│  │  Models: Investigation                        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Layers

### 1. API Layer (`backend/app/api/v1/`)

FastAPI route handlers organized by resource:

| File | Endpoints | Purpose |
|------|-----------|---------|
| `investigations.py` | `POST /investigations`, `GET /investigations`, `GET /investigations/{id}`, `DELETE /investigations/{id}` | CRUD for investigations; auto-triggers runner on POST |
| `investigations.py` | `WS /investigations/ws/{id}` | WebSocket for real-time progress streaming |
| `tools.py` | `GET /tools`, `GET /tools/categories` | List available OSINT tools and categories |
| `reports.py` | `POST /reports/generate/{id}`, `GET /reports/status` | Trigger LLM report generation, check LLM availability |

All routes are prefixed with `/api/v1` via the router aggregator.

### 2. WebSocket Manager (`backend/app/ws/manager.py`)

In-memory connection manager for real-time investigation progress:

```python
class WebSocketManager:
    async def connect(investigation_id, ws)   # Accept WS, track connection
    def disconnect(investigation_id, ws)       # Remove stale connections
    async def broadcast(investigation_id, msg) # JSON-serialized to all listeners
```

- Auto-cleans stale connections on send failure
- Each investigation has its own set of listeners
- Messages: `{"type": "status"|"tool_progress", "status": "...", "tool": "..."}`

### 3. Orchestration Layer (`backend/app/orchestration/`)

**Pipeline (`pipeline.py`):**
- Creates an execution plan (DAG) based on seed type
- Email: holehe → ghunt → h8mail → theHarvester → (extract usernames) → sherlock → maigret
- Username: sherlock → maigret → socid_extractor → instaloader → snscrape (twitter) → snscrape (reddit)
- Domain: theHarvester → emailfinder → censys → shodan → waybackpy

**Dispatcher (`dispatcher.py`):**
- Runs tool adapters in parallel respecting dependencies
- Handles async and sync progress callbacks
- Per-tool timeout (60s default via `run_cli`)
- Tracks stalled pipelines (dependencies never met)

**Runner (`runner.py`):**
- `InvestigationRunner.run()` — full lifecycle manager
- Creates own DB session via `async_session()` for background execution
- Merge all tool results into a single dict
- Invoke graph builder → Invoke LLM report (if configured) → Save to DB
- Auto-triggered via `asyncio.ensure_future` on `POST /investigations`
- Dedup protection: skips if investigation_id already running
- Graceful error handling: per-tool errors don't crash the whole investigation

### 4. Graph Builder (`backend/app/graph/builder.py`)

Extracts entities from tool results and builds a Cytoscape.js-compatible graph:

**Entity extraction per tool:**
| Tool | Node Type | Edge Label |
|------|-----------|------------|
| holehe | `service` | `registered_on` |
| ghunt | `person` | `google_account` |
| h8mail | `breach` | `found_in_breach` |
| emailfinder | `email` | `associated_email` |
| theHarvester | `email`, `domain`, `ip` | `found_email`, `host`, `resolves_to` |
| sherlock/maigret | `social` | `found_on_{site}` |
| instaloader | `social` | `instagram_profile` |
| snscrape | `social` | `content_on_{platform}` |
| censys/shodan | `service` | `discovered_by_{tool}` |
| waybackpy | `archive` | `wayback_snapshot` |

**Helper functions:**
- `extract_usernames(results)` — deduplicated list from all tool outputs
- `extract_emails(results)` — deduplicated list including `value` field checks
- `extract_domains(results)` — deduplicated list excluding IP addresses

### 5. Tool Adapters (`backend/app/tools/`)

Each adapter wraps a CLI tool or Python library. All implement `BaseTool`:

```python
class BaseTool(ABC):
    name: str                    # Unique identifier
    category: ToolCategory       # email|username|social|domain|phone|data_breach
    description: str             # Human-readable description
    enabled: bool                # Can be disabled by user

    async def run(self, target: str, **kwargs) -> ToolResult
```

**ToolResult** structure:
```python
@dataclass
class ToolResult:
    tool_name: str
    category: ToolCategory
    status: str                  # "success" | "partial" | "error"
    raw_data: dict               # Full CLI/API output
    normalized: list[dict]       # Structured findings
    error: Optional[str]
    duration_ms: int
```

**Registered Tools (15 total):**

| Category | Tool | Method | Target Type | Output |
|----------|------|--------|-------------|--------|
| Email | `holehe` | CLI subprocess | email | Services where email is registered |
| Email | `ghunt` | CLI subprocess | email | Google account info (name, id, photo) |
| Email | `h8mail` | CLI subprocess | email | Data breach occurrences, paste findings |
| Email | `emailfinder` | CLI subprocess | domain | Emails associated with domain |
| Email | `theHarvester` | CLI subprocess | domain | Emails, subdomains, hosts, IPs |
| Username | `sherlock` | CLI subprocess | username | Social media accounts found |
| Username | `maigret` | CLI subprocess | username | Sites where username exists (2500+) |
| Username | `socid_extractor` | CLI subprocess | username | Extracted social IDs from profiles |
| Social | `instaloader` | CLI subprocess | username | Instagram posts, followers, following |
| Social | `facebook_scraper` | Python lib | username | Facebook profile data |
| Social | `snscrape` | CLI subprocess | username | Tweets, Reddit posts, Telegram |
| Domain | `theHarvester` | CLI subprocess | domain | Subdomains, emails, hosts |
| Domain | `censys` | CLI subprocess | domain | SSL certs, open ports, services |
| Domain | `shodan` | CLI subprocess | domain | IoT devices, services, vulns |
| Domain | `waybackpy` | Python lib | url | Historical snapshots, hidden endpoints |

### 6. LLM Service (`backend/app/llm/`)

Uses the OpenAI Python SDK pointed at Fanar's API:

```python
client = OpenAI(
    api_key=settings.fanar_api_key,
    base_url="https://api.fanar.qa/v1"
)
```

**Components:**
- `service.py` — `LLMService` class with `generate_report()` and `generate_summary()`
- `prompts.py` — System prompts for different report types
- Singleton `llm_service` instance for the app

**Report Types (via prompts):**
1. Full intelligence report (executive summary + all findings)
2. Executive summary (3 paragraphs)
3. Social profile analysis
4. Data breach analysis

### 7. Data Layer (`backend/app/db/`)

| File | Purpose |
|------|---------|
| `base.py` | SQLAlchemy `DeclarativeBase` |
| `session.py` | Async engine + session factory, `get_db` dependency |

**Model: Investigation**
```python
class Investigation(Base):
    id: str                    # UUID
    seed: str                  # Original search term (email, username, domain)
    type: str                  # email|username|domain|phone
    status: str                # pending|running|completed|failed
    created_at: datetime
    completed_at: datetime?
    tool_results: dict?        # Merged output from all tools
    graph: dict?               # Node/edge graph for visualization
    report: str?               # LLM-generated report
    error: str?                # Error message if failed
```

### 8. Frontend (`frontend/src/`)

| Directory | Purpose |
|-----------|---------|
| `components/Layout/` | Sidebar + main content wrapper |
| `components/Dashboard/` | Stats cards + recent investigations list |
| `components/Investigation/` | New investigation form + detail view |
| `components/Graph/` | Cytoscape.js relationship graph (future) |
| `components/Report/` | LLM report viewer (future) |
| `services/api.ts` | Axios client for all backend calls |
| `store/app.ts` | Zustand state (sidebar toggle) |
| `types/index.ts` | Full TypeScript type definitions |

---

## Data Flow: Full Investigation

```
1. User enters "john@example.com" → selects "Email" type
2. Frontend → POST /api/v1/investigations {seed, type}
3. Backend → creates Investigation (status: "pending") → returns {id}
4. Backend → asyncio.ensure_future(runner.run(id, seed, type))
5. Frontend → opens WebSocket /api/v1/investigations/ws/{id}
6. Runner → updates status to "running" → broadcasts via WS

7. Orchestrator → builds execution DAG:

   john@example.com
   ├── holehe       ─── services found
   ├── ghunt        ─── google profile
   ├── h8mail       ─── data breaches
   ├── theHarvester ─── domain extraction
   │
   ├── (extract domain: example.com)
   │   └── theHarvester(d)  ─── subdomains
   │   ├── censys           ─── ssl/ports
   │   ├── shodan           ─── services
   │   └── waybackpy        ─── history
   │
   ├── (extract usernames from emails)
   │   ├── sherlock  ─── social accounts
   │   ├── maigret   ─── deep search
   │   └── instaloader ─── instagram

8. Each tool runs via asyncio.create_subprocess_exec (parallel where possible)
9. WS broadcasts: {"type": "tool_progress", "tool": "holehe", "status": "running"}
10. Results merged → tool_results dict
11. Graph builder → creates node/edge JSON → graph dict
12. LLM service → generates report (if FANAR_API_KEY set)
13. WS broadcasts: {"type": "status", "status": "completed"}
14. Investigation.status = "completed"
15. Frontend → polls/ws → receives completion → fetches investigation detail
```

---

## Container Architecture

```
┌──────────────────────────────────────────────┐
│  Docker Image (meower:latest)                 │
│                                                │
│  Stage 1 (frontend-builder):                   │
│    FROM node:22-alpine                         │
│    npm ci && npm run build                     │
│    → /build/frontend/dist                      │
│                                                │
│  Stage 2 (runtime):                            │
│    FROM python:3.14-slim                       │
│    COPY --from=1 /build/frontend/dist ./dist   │
│    pip install -r requirements.txt             │
│    uvicorn app.main:app                        │
│                                                │
│  Volumes:                                      │
│    /app/data  ← SQLite DB (persistence)        │
│                                                │
│  Env Vars:                                     │
│    FANAR_API_KEY  ← Required for LLM          │
│    DATABASE_URL   ← Default: sqlite://data.db  │
└──────────────────────────────────────────────┘
```

Image size: ~200MB (Python slim + compiled frontend assets)

---

## Key Design Decisions

### Why not microservices?
Single container is simpler for the user. All OSINT tools run CLI subprocesses from the same Python process. No need for service discovery, message queues, or distributed tracing.

### Why async subprocess (not subprocess.run)?
All tool calls use `asyncio.create_subprocess_exec` to avoid blocking the event loop. Multiple tools can run concurrently within the same investigation.

### Why normalized + raw_data dual output?
- `raw_data` preserves the original CLI output (for debugging, power users)
- `normalized` provides a consistent schema (for the LLM, graph builder, and UI)
- LLM gets the normalized data; the graph builder focuses on entities

### Why SQLite instead of PostgreSQL?
SQLite is file-based, requires zero configuration, and lives inside the container. For an OSINT tool handling personal investigations (not a multi-tenant SaaS), SQLite is more than sufficient.

### Why Fanar instead of OpenAI?
User's explicit choice. Fanar is hosted in Qatar, OpenAI-compatible, with 50 req/min rate limit. The OpenAI SDK is reused with a different `base_url`.

### Why ensure_future for investigation runner?
The `POST /investigations` endpoint creates the DB record and returns immediately. The investigation runs as a background task via `asyncio.ensure_future`. The runner creates its own DB session to avoid request-scoped session issues. The WebSocket provides real-time progress.

---

## Testing Strategy

```
tests/
├── conftest.py                 # anyio_backend = "asyncio"
├── test_api.py                 # 8 tests: CRUD investigations, tools, health
├── test_llm.py                 # 4 tests: mock report gen, context building, no-key error
├── test_graph.py               # 26 tests: entity extraction, edge cases, helpers
├── test_ws.py                  # 11 tests: WS connect/disconnect/broadcast edge cases
├── test_runner.py              # 11 tests: merge, dedup, error handling, cleanup
├── test_orchestration.py       # 10 tests: pipeline builder, dispatcher DAG
└── test_tools/                 # 43 tests: runner + adapters per tool
    ├── test_runner.py
    ├── test_holehe.py
    ├── test_sherlock.py
    └── ...
```

**Total: 113 tests**

**Principles:**
- Tool adapters mock subprocess calls via `asyncio.create_subprocess_exec` → `AsyncMock`
- API tests use `httpx.AsyncClient` with `ASGITransport`; runner mocked for speed
- Graph/WS/Runner tests are pure unit tests with minimal mocking
- DB tests use per-fixture table creation/drop
- LLM tests mock `OpenAI.chat.completions.create`

---

## Future Architecture

1. **Person model** — Cross-investigation entity resolution (same email across investigations)
2. **Celery workers** — Heavy investigations without blocking the event loop
3. **Export plugins** — PDF (WeasyPrint), CSV, STIX/TAXII
4. **Plugin system** — Community tool adapters via Python entrypoints
5. **Compiled report caching** — LLM report results cached to avoid re-generation
