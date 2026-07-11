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
│  │  (api/v1/)   │  │  (core/)     │  │  (future)  │  │
│  └──────┬───────┘  └──────────────┘  └────────────┘  │
│         │                                             │
│  ┌──────▼─────────────────────────────────────────┐  │
│  │           Orchestration Layer                    │  │
│  │  (orchestration/pipeline.py + dispatcher.py)    │  │
│  │  Builds DAG → runs tools in order → merges      │  │
│  └──────┬──────────┬──────────┬──────────┬────────┘  │
│         │          │          │          │           │
│  ┌──────▼──┐ ┌────▼──┐ ┌────▼──┐ ┌────▼──┐        │
│  │  Email   │ │Username│ │ Social │ │ Domain │        │
│  │  Tools   │ │ Tools  │ │ Tools  │ │ Tools  │        │
│  │  (5)     │ │ (3)    │ │ (3)    │ │ (4)    │        │
│  └─────────┘ └────────┘ └────────┘ └────────┘        │
│         │                                             │
│  ┌──────▼─────────────────────────────────────────┐  │
│  │              LLM Service (Fanar)                │  │
│  │  app/llm/service.py + prompts.py               │  │
│  │  OpenAI SDK → api.fanar.qa/v1                  │  │
│  └──────────────┬──────────────────────────────────┘  │
│                 │                                     │
│  ┌──────────────▼──────────────────────────────────┐  │
│  │           Data Layer                             │  │
│  │  SQLAlchemy (async) + SQLite                    │  │
│  │  Models: Investigation, Person (future)         │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Layers

### 1. API Layer (`backend/app/api/v1/`)

FastAPI route handlers organized by resource:

| File | Endpoints | Purpose |
|------|-----------|---------|
| `investigations.py` | `POST /investigations`, `GET /investigations`, `GET /investigations/{id}`, `DELETE /investigations/{id}` | CRUD for investigations |
| `tools.py` | `GET /tools`, `GET /tools/categories` | List available OSINT tools and categories |
| `reports.py` | `POST /reports/generate/{id}`, `GET /reports/status` | Trigger LLM report generation, check LLM availability |

All routes are prefixed with `/api/v1` via the router aggregator.

### 2. Orchestration Layer (`backend/app/orchestration/`)

**Pipeline (`pipeline.py`):**
- Creates an execution plan (DAG) based on seed type
- Example: email seed → holehe → ghunt → h8mail → theHarvester → (extract usernames) → sherlock → maigret → instagram

**Dispatcher (`dispatcher.py`):**
- Runs tool adapters in parallel respecting dependencies
- Streams progress updates via WebSocket (future)

### 3. Tool Adapters (`backend/app/tools/`)

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

### 4. LLM Service (`backend/app/llm/`)

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

### 5. Data Layer (`backend/app/db/`)

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

### 6. Frontend (`frontend/src/`)

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
4. Frontend → opens WebSocket /ws/{id} (future)
5. Orchestrator → builds execution DAG:

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
   │   ├── instaloader ─── instagram
   │   └── facebook_scraper ─── facebook

6. Each tool runs via asyncio.create_subprocess_exec (parallel where possible)
7. Results merged → Investigation.tool_results = {...}
8. Graph builder → creates node/edge JSON → Investigation.graph = {...}
9. LLM service → generates report → Investigation.report = "..."
10. Investigation.status = "completed"
11. Frontend → displays results, graph, report
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

---

## Testing Strategy

```
tests/
├── conftest.py           # anyio_backend = "asyncio"
├── test_api.py           # 8 tests: CRUD investigations, tools list, health
├── test_llm.py           # 4 tests: mock report gen, context building, no-key error
└── test_tools/           # Tool adapter tests (one per adapter)
    ├── __init__.py
    ├── test_holehe.py
    ├── test_sherlock.py
    └── ...
```

**Principles:**
- Tool adapters mock subprocess calls via `asyncio.create_subprocess_exec` → `AsyncMock`
- API tests use `httpx.AsyncClient` with `ASGITransport`
- DB tests use per-fixture table creation/drop
- LLM tests mock `OpenAI.chat.completions.create`

---

## Future Architecture

1. **WebSocket streaming** — Real-time progress as tools execute
2. **Celery workers** — Heavy investigations without blocking
3. **Person model** — Entity extraction + graph database (future)
4. **Export plugins** — PDF (WeasyPrint), CSV, STIX/TAXII
5. **Plugin system** — Community tool adapters via Python entrypoints
