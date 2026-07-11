# 🕵️ Meower — OSINT Intelligence Gathering Platform

## Execution Plan

> **Vision:** A unified OSINT platform that orchestrates existing tools (theHarvester, Sherlock, Holehe, Maigret, GHunt, etc.), correlates their output, builds a relationship graph around a target, and uses an LLM to generate plain-English intelligence reports.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Tech Stack](#2-tech-stack)
3. [Phase 1 — Foundation & Project Structure](#3-phase-1--foundation--project-structure)
4. [Phase 2 — Tool Adapters (The Core)](#4-phase-2--tool-adapters-the-core)
5. [Phase 3 — Investigation Engine & Orchestrator](#5-phase-3--investigation-engine--orchestrator)
6. [Phase 4 — Person Graph & Relationship Tree](#6-phase-4--person-graph--relationship-tree)
7. [Phase 5 — LLM Layer (Report Generation)](#7-phase-5--llm-layer-report-generation)
8. [Phase 6 — React Frontend](#8-phase-6--react-frontend)
9. [Phase 7 — Deployment & DevOps](#9-phase-7--deployment--devops)
10. [Tool Integration Checklist](#10-tool-integration-checklist)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  Dashboard │ Investigation Panel │ Graph View │ Reports  │
└──────────────────────┬──────────────────────────────────┘
                       │  REST / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Routes  │ │  Auth    │ │  WS Mgr  │ │  Export  │   │
│  └────┬─────┘ └──────────┘ └──────────┘ └──────────┘   │
│       │                                                │
│  ┌────▼─────────────────────────────────────────────┐  │
│  │              Orchestrator Layer                   │  │
│  │    Pipeline Builder │ Task Dispatcher │ Cache     │  │
│  └────┬──────────┬──────────┬──────────┬──────────┘  │
│       │          │          │          │             │
│  ┌────▼──┐ ┌────▼──┐ ┌────▼──┐ ┌────▼──┐           │
│  │ Email │ │Social │ │Domain │ │Username│           │
│  │ Tools │ │ Tools │ │ Tools │ │ Tools  │           │
│  └───────┘ └───────┘ └───────┘ └───────┘           │
│       │                                             │
│  ┌────▼─────────────────────────────────────────┐   │
│  │            LLM Service                        │   │
│  │  Ollama (local) │ OpenAI API │ Prompt Mgmt   │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Separation of Concerns

| Layer | Responsibility |
|-------|---------------|
| **API Routes** | HTTP/WS entry points, validation, auth |
| **Orchestrator** | Pipeline logic, parallel dispatch, result merging |
| **Tool Adapters** | Wrap CLI tools as standardised Python interfaces |
| **LLM Service** | Prompt construction, model routing, report generation |
| **Data Layer** | SQLite/Postgres models, repositories, cache |
| **Frontend** | UI components, state management, visualisation |

---

## 2. Tech Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| **Backend** | FastAPI + Uvicorn | Async, auto-docs, Pydantic validation |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Simple start, scalable |
| **ORM** | SQLAlchemy + Alembic | Mature, migrations |
| **Task Queue** | Celery + Redis (optional) | Long-running investigations |
| **LLM** | Ollama (local) + OpenAI (fallback) | Privacy-first, flexible |
| **Frontend** | React + Vite + Tailwind CSS | Fast dev, modern UI |
| **Graph Vis** | Cytoscape.js or React Flow | Relationship trees |
| **Auth** | JWT + OAuth2 | Simple, standard |
| **Container** | Docker + Docker Compose | Reproducible |

---

## 3. Phase 1 — Foundation & Project Structure

### 3.1 Directory Layout

```
meower/
├── backend/
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   │   ├── v1/
│   │   │   │   ├── investigations.py
│   │   │   │   ├── tools.py
│   │   │   │   ├── reports.py
│   │   │   │   └── auth.py
│   │   ├── core/             # Config, dependencies
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/           # SQLAlchemy models
│   │   │   ├── investigation.py
│   │   │   ├── result.py
│   │   │   └── person.py
│   │   ├── schemas/          # Pydantic request/response
│   │   │   ├── investigation.py
│   │   │   └── report.py
│   │   ├── orchestration/    # Pipeline engine
│   │   │   ├── pipeline.py
│   │   │   └── dispatcher.py
│   │   ├── tools/            # Tool adapters
│   │   │   ├── base.py       # Abstract base class
│   │   │   ├── theharvester.py
│   │   │   ├── sherlock.py
│   │   │   ├── holehe.py
│   │   │   ├── maigret.py
│   │   │   ├── ghunt.py
│   │   │   ├── h8mail.py
│   │   │   ├── emailfinder.py
│   │   │   ├── instaloader.py
│   │   │   ├── facebook_scraper.py
│   │   │   ├── snscrape.py
│   │   │   ├── censys.py
│   │   │   ├── shodan.py
│   │   │   ├── waybackpy.py
│   │   │   └── socid_extractor.py
│   │   ├── llm/              # LLM service
│   │   │   ├── service.py
│   │   │   ├── prompts.py
│   │   │   └── models.py
│   │   ├── graph/            # Relationship graph builder
│   │   │   ├── builder.py
│   │   │   └── serializer.py
│   │   └── db/
│   │       ├── session.py
│   │       └── base.py
│   ├── alembic/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   ├── Dashboard/
│   │   │   ├── Investigation/
│   │   │   ├── Graph/
│   │   │   └── Report/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
│
└── README.md
```

### 3.2 Setup Commands

```bash
# Backend
mkdir -p meower/backend && cd meower/backend
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy alembic pydantic pydantic-settings
pip install openai ollama celery redis httpx aiofiles
pip install python-jose[cryptography] passlib[bcrypt] python-multipart

# Freeze everything
pip freeze > requirements.txt

# Frontend
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install axios @tanstack/react-query zustand react-router-dom
npm install cytoscape react-cytoscapejs tailwindcss @tailwindcss/vite
npm install recharts lucide-react
```

---

## 4. Phase 2 — Tool Adapters (The Core)

### 4.1 Abstract Base Class

Each tool wraps its CLI or Python API into a uniform interface:

```python
# backend/app/tools/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

class ToolCategory(Enum):
    EMAIL = "email"
    USERNAME = "username"
    SOCIAL = "social"
    DOMAIN = "domain"
    PHONE = "phone"
    DATA_BREACH = "data_breach"

@dataclass
class ToolResult:
    tool_name: str
    category: ToolCategory
    status: str           # "success" | "partial" | "error"
    raw_data: dict        # tool-specific output
    normalized: list[dict] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0

class BaseTool(ABC):
    name: str
    category: ToolCategory

    @abstractmethod
    async def run(self, target: str, **kwargs) -> ToolResult:
        ...
```

### 4.2 Tool Implementation Examples

#### Holehe (Email → Service Registration Check)

```python
# backend/app/tools/holehe.py

import asyncio
from .base import BaseTool, ToolResult, ToolCategory

class HoleheTool(BaseTool):
    name = "holehe"
    category = ToolCategory.EMAIL

    async def run(self, target: str, **kwargs) -> ToolResult:
        proc = await asyncio.create_subprocess_exec(
            "holehe", target, "--only-used", "--no-color",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        # Parse output → list of {service, exists, email}
        ...
```

#### Sherlock (Username → Social Profiles)

```python
# backend/app/tools/sherlock.py

class SherlockTool(BaseTool):
    name = "sherlock"
    category = ToolCategory.USERNAME

    async def run(self, target: str, **kwargs) -> ToolResult:
        proc = await asyncio.create_subprocess_exec(
            "sherlock", target, "--print-found", "--no-color",
            "--txt", "--folderoutput", "/tmp/sherlock",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        # Parse sherlock txt output → list of {site, url, username}
        ...
```

#### TheHarvester (Domain/Email → Subdomains, Emails, Hosts)

```python
# backend/app/tools/theharvester.py

class TheHarvesterTool(BaseTool):
    name = "theharvester"
    category = ToolCategory.DOMAIN

    async def run(self, target: str, **kwargs) -> ToolResult:
        domain = kwargs.get("domain", target)
        proc = await asyncio.create_subprocess_exec(
            "theHarvester", "-d", domain, "-b", "all", "-f", "/tmp/harvest.html",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        # Parse HTML output → emails, hosts, subdomains, ips
        ...
```

#### GHunt (Email → Google Account Info)

```python
# backend/app/tools/ghunt.py

class GHuntTool(BaseTool):
    name = "ghunt"
    category = ToolCategory.EMAIL

    async def run(self, target: str, **kwargs) -> ToolResult:
        proc = await asyncio.create_subprocess_exec(
            "ghunt", "email", target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        # Parse JSON → display_name, google_id, profile_pic, etc.
        ...
```

#### Maigret (Username → 2500+ Sites)

```python
# backend/app/tools/maigret.py

class MaigretTool(BaseTool):
    name = "maigret"
    category = ToolCategory.USERNAME

    async def run(self, target: str, **kwargs) -> ToolResult:
        proc = await asyncio.create_subprocess_exec(
            "maigret", target, "--json", "/tmp/maigret_out.json",
            "--no-recursion", "--timeout", "15",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        # Parse JSON output → list of {site, url, status}
        ...
```

### 4.3 Tool Registry

```python
# backend/app/tools/__init__.py

from .holehe import HoleheTool
from .sherlock import SherlockTool
from .theharvester import TheHarvesterTool
from .maigret import MaigretTool
from .ghunt import GHuntTool
from .h8mail import H8MailTool
from .emailfinder import EmailFinderTool
from .instaloader import InstaloaderTool
from .facebook_scraper import FacebookScraperTool
from .snscrape import SnscrapeTool
from .censys import CensysTool
from .shodan import ShodanTool
from .waybackpy import WaybackpyTool
from .socid_extractor import SocidExtractorTool
from .base import ToolCategory

TOOL_REGISTRY = [
    HoleheTool(),
    SherlockTool(),
    TheHarvesterTool(),
    MaigretTool(),
    GHuntTool(),
    H8MailTool(),
    EmailFinderTool(),
    InstaloaderTool(),
    FacebookScraperTool(),
    SnscrapeTool(),
    CensysTool(),
    ShodanTool(),
    WaybackpyTool(),
    SocidExtractorTool(),
]

def get_tools_by_category(category: ToolCategory) -> list[BaseTool]:
    return [t for t in TOOL_REGISTRY if t.category == category]
```

---

## 5. Phase 3 — Investigation Engine & Orchestrator

### 5.1 Investigation Pipeline

An investigation is a multi-step pipeline triggered by a **seed** (email, username, domain, phone).

```
Seed: "john@example.com"
  │
  ├──▶ HOLEHE         → {services: [twitter, github, ...]}
  ├──▶ GHUNT          → {google_id, display_name, profile_pic}
  ├──▶ H8MAIL         → {breaches: [collection1, ...]}
  ├──▶ THEHARVESTER   → (domain extraction from email)
  ├──▶ EMAILFINDER    → (associated emails)
  │
  ├──▶ EXTRACT USERNAME from results
  │     │
  │     ├──▶ SHERLOCK  → {sites: [twitter/john, github/john, ...]}
  │     ├──▶ MAIGRET   → {sites: [linkedin/john, ...]}
  │     ├──▶ SOCID     → {social_ids, cross-links}
  │     │
  │     ├──▶ INSTALOADER    → {instagram posts, followers}
  │     ├──▶ FACEBOOK_SCRAPER → {facebook profile, friends}
  │     ├──▶ SNSCRAPE        → {tweets, reddit posts}
  │
  ├──▶ EXTRACT DOMAIN from email
  │     │
  │     ├──▶ THEHARVESTER → {subdomains, ips, hosts}
  │     ├──▶ CENSYS      → {ssl certs, open ports}
  │     ├──▶ SHODAN      → {services, vulns}
  │     ├──▶ WAYBACKPY   → {historical pages, hidden endpoints}
  │
  └──▶ MERGE → GRAPH BUILD → LLM REPORT
```

### 5.2 Orchestrator Design

```python
# backend/app/orchestration/pipeline.py

from dataclasses import dataclass
from enum import Enum

class InvestigationType(str, Enum):
    EMAIL = "email"
    USERNAME = "username"
    DOMAIN = "domain"
    PHONE = "phone"
    FULL = "full"          # expand whatever we can

@dataclass
class InvestigationPlan:
    seed: str
    type: InvestigationType
    steps: list[dict]      # [{tool, target, depends_on}]
```

**Orchestrator logic:**

```python
class Orchestrator:
    def create_plan(self, seed: str, type: InvestigationType) -> InvestigationPlan:
        """Dynamically build a DAG of tool executions based on seed type."""

    async def execute(self, plan: InvestigationPlan) -> InvestigationResult:
        """Run tool steps in parallel where dependencies allow.
           Stream progress via WebSocket to frontend."""
```

**Parallel execution with dependency graph:**

```python
import asyncio
from collections import deque

class Dispatcher:
    async def run_dag(self, steps: list[dict], ws_stream=None):
        ready = deque([s for s in steps if not s.get("depends_on")])
        in_progress = {}
        results = {}
        while ready or in_progress:
            # Launch all ready steps concurrently
            tasks = [self._run_tool(step) for step in ready]
            completed = await asyncio.gather(*tasks)
            for step, result in zip(ready, completed):
                results[step["id"]] = result
                if ws_stream:
                    await ws_stream.send_json(step | {"status": "done", "result": result.model_dump()})
            # Unblock dependent steps
            newly_ready = self._unblock(steps, results)
            ready = deque(newly_ready)
```

### 5.3 Investigation Model

```python
# backend/app/models/investigation.py

class Investigation(Base):
    id: uuid.UUID
    seed: str                       # "john@example.com"
    type: InvestigationType
    status: str                     # "running" | "completed" | "failed"
    created_at: datetime
    completed_at: datetime | None
    result: JSON | None             # Merged result from all tools
    graph: JSON | None              # Person/entity graph
    report: str | None              # LLM-generated report
```

---

## 6. Phase 4 — Person Graph & Relationship Tree

### 6.1 Entity Model

Every discovered identity becomes a node:

```
Person Node:
  - name, email, username, phone
  - google_id, social_ids[]
  - profile_urls[]
  - associated_domains[]
  - data_breaches[]
  - risk_score

Domain Node:
  - domain, subdomains, ips
  - registrant_email
  - technologies
  - ssl_info

Edge Types:
  - HAS_EMAIL, HAS_USERNAME
  - REGISTERED_DOMAIN
  - ASSOCIATED_ACCOUNT
  - DATA_BREACH
  - SOCIAL_CONNECTION
```

### 6.2 Graph Builder

```python
# backend/app/graph/builder.py

class GraphBuilder:
    def build(self, results: dict) -> dict:
        """
        Input: merged results from all tools
        Output: { nodes: [...], edges: [...] } for Cytoscape.js
        """
        # 1. Extract all unique entities (people, emails, domains, urls)
        # 2. Link entities via relationships
        # 3. Return graph JSON
```

Example output:

```json
{
  "nodes": [
    { "data": { "id": "john@example.com", "label": "john@example.com", "type": "email" }},
    { "data": { "id": "john_gh", "label": "GitHub: john", "type": "social", "url": "https://github.com/john" }},
    { "data": { "id": "example.com", "label": "example.com", "type": "domain" }}
  ],
  "edges": [
    { "data": { "source": "john@example.com", "target": "john_gh", "label": "has_account" }},
    { "data": { "source": "john@example.com", "target": "example.com", "label": "registered" }}
  ]
}
```

---

## 7. Phase 5 — LLM Layer (Report Generation)

### 7.1 Architecture

```
LLM Service
├── Ollama (local, default)   → Llama 3 / Mistral / DeepSeek
├── OpenAI API (fallback)     → GPT-4o / GPT-4o-mini
└── Prompt Templates
    ├── executive_summary.md
    ├── threat_analysis.md
    ├── social_profile.md
    └── recommendations.md
```

### 7.2 Report Types

| Report | Content |
|--------|---------|
| **Executive Summary** | Who is this person? Key findings in 3 paragraphs |
| **Digital Footprint** | All discovered accounts, services, exposures |
| **Data Breach Report** | Which breaches, what data leaked, passwords found |
| **Social Graph Analysis** | Network connections, influence, communities |
| **Risk Assessment** | Privacy score, exposure level, recommendations |
| **Full Dossier** | Comprehensive PDF with all findings |

### 7.3 Implementation

```python
# backend/app/llm/service.py

class LLMService:
    def __init__(self):
        self.provider = self._detect_provider()

    def _detect_provider(self) -> str:
        if shutil.which("ollama"):
            return "ollama"
        return "openai"

    async def generate_report(self, data: dict, report_type: str) -> str:
        prompt = self._load_prompt(report_type)
        context = self._build_context(data)
        full_prompt = f"{prompt}\n\n## Raw Intelligence Data\n{context}"

        if self.provider == "ollama":
            return await self._call_ollama(full_prompt)
        else:
            return await self._call_openai(full_prompt)

    async def _call_ollama(self, prompt: str) -> str:
        import ollama
        response = ollama.chat(model="llama3.1", messages=[
            {"role": "system", "content": "You are an expert OSINT analyst."},
            {"role": "user", "content": prompt}
        ])
        return response["message"]["content"]

    def _build_context(self, data: dict) -> str:
        """Format raw tool output into LLM-friendly context."""
        sections = []
        for tool, result in data.get("tool_results", {}).items():
            if result.get("status") == "success":
                sections.append(f"=== {tool} ===")
                sections.append(json.dumps(result.get("normalized", []), indent=2))
        return "\n".join(sections)
```

### 7.4 System Prompt (Example)

```markdown
You are Meower AI, an expert OSINT analyst and intelligence reporter.
Given raw OSINT data gathered from multiple tools, produce a clear,
professional intelligence report.

Guidelines:
1. Start with an executive summary of who the target is
2. List all discovered digital identities (email, usernames, profiles)
3. Highlight any data breaches or security exposures
4. Map social connections and relationships
5. Assess overall exposure level: LOW / MEDIUM / HIGH / CRITICAL
6. Provide actionable recommendations for further investigation
7. Be factual — cite sources where possible
8. Flag any contradictions or suspicious findings
```

---

## 8. Phase 6 — React Frontend

### 8.1 Route Structure

```
/                     → Dashboard (recent investigations, stats)
/investigate          → New investigation form
/investigation/:id    → Live progress + results view
/investigation/:id/graph → Relationship graph (full screen)
/investigation/:id/report → LLM-generated report
/history              → Past investigations
/settings             → API keys, LLM config, tool toggles
```

### 8.2 Key Components

| Component | Description |
|-----------|-------------|
| `InvestigationForm` | Seed input with type selector + tool toggles |
| `ProgressPanel` | Real-time log of tool execution via WebSocket |
| `ResultCard` | Compact display of single tool output |
| `GraphCanvas` | Interactive Cytoscape.js relationship graph |
| `ReportViewer` | Markdown-rendered LLM report with export buttons |
| `DashboardStats` | Summary cards, recent activity, trends |

### 8.3 Real-Time Progress (WebSocket)

```typescript
// frontend/src/hooks/useInvestigation.ts

export function useInvestigation(id: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [progress, setProgress] = useState<Step[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${id}`);
    ws.onmessage = (event) => {
      const step = JSON.parse(event.data);
      setProgress(prev => [...prev, step]);
    };
    wsRef.current = ws;
    return () => ws.close();
  }, [id]);

  return { progress };
}
```

### 8.4 Graph Visualization

```bash
npm install cytoscape react-cytoscapejs
```

```tsx
// frontend/src/components/Graph/GraphCanvas.tsx

import CytoscapeComponent from 'react-cytoscapejs';

const elements = [
  { data: { id: 'email1', label: 'john@example.com', type: 'email' }},
  { data: { id: 'gh1', label: 'GitHub: john', type: 'social' }},
  { data: { id: 'e1', label: 'has_account', source: 'email1', target: 'gh1' }}
];

const layout = { name: 'breadthfirst', directed: true };

export function GraphCanvas() {
  return (
    <CytoscapeComponent
      elements={elements}
      layout={layout}
      style={{ width: '100%', height: '600px' }}
      stylesheet={[
        { selector: 'node[type="email"]', style: { 'background-color': '#3b82f6', label: 'data(label)' }},
        { selector: 'node[type="social"]', style: { 'background-color': '#10b981', label: 'data(label)' }},
        { selector: 'node[type="domain"]', style: { 'background-color': '#f59e0b', label: 'data(label)' }},
        { selector: 'edge', style: { 'line-color': '#6b7280', 'target-arrow-color': '#6b7280', 'target-arrow-shape': 'triangle' }}
      ]}
    />
  );
}
```

### 8.5 UI Screens (Wireframes)

**Dashboard:**
```
┌──────────────────────────────────────────────────────┐
│  🕵️ Meower  │  New Investigation  │  History  │  ⚙️   │
├──────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Total    │  │ Complete │  │ Exposed  │           │
│  │ 47       │  │ 32       │  │ HIGH: 12 │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                       │
│  Recent Investigations:                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │ john@example.com    ██████████ 100%  📊📄      │ │
│  │ jane_doe            ████████░░ 80%   📊📄      │ │
│  │ acme.com            ██████████ 100%  📊📄      │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Investigation Detail:**
```
┌──────────────────────────────────────────────────────┐
│  ← Back    john@example.com    Running: 4/12 tools   │
├──────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │ Graph View │  │ Raw Data   │  │ LLM Report │     │
│  └────────────┘  └────────────┘  └────────────┘     │
│                                                       │
│  📋 Progress:                                         │
│  ✅ holehe — found on 14 services                     │
│  ✅ ghunt — Google account: John Doe                  │
│  ✅ sherlock — found on 23 platforms                  │
│  🔄 maigret — scanning...                             │
│  ⏳ h8mail — waiting...                               │
│  ⏳ theharvester — waiting...                         │
│                                                       │
│  🎯 Key Findings:                                     │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 📧 Email registered on Twitter, GitHub, Reddit... │ │
│  │ 🔓 Data breach in Collection #1 (password found)  │ │
│  │ 🌐 Domain: example.com (Cloudflare, 3 subdomains) │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

## 9. Phase 7 — Deployment & DevOps

### 9.1 Docker Compose

```yaml
# docker-compose.yml

version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./meower.db
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./backend:/app
      - meower_data:/app/data
    depends_on:
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  meower_data:
  ollama_data:
```

### 9.2 Environment Variables

```bash
# Backend .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/meower
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-...          # optional fallback
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

### 9.3 Installation Script

```bash
# setup.sh — One-command setup

echo "🚀 Setting up Meower OSINT Platform..."

# 1. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 2. Pull LLM model
ollama pull llama3.1:8b

# 3. Frontend
cd ../frontend
npm install

# 4. Run
echo "✅ Done! Run: docker compose up"
```

---

## 10. Complete Execution Timeline

| Phase | Tasks | Est. Time | Dependencies |
|-------|-------|-----------|-------------|
| **P1** | Project scaffold, FastAPI skeleton, DB models, Dockerfile | 1 day | None |
| **P2** | Tool adapters (16 tools), parser for each output format | 3 days | P1 |
| **P3** | Investigation pipeline with DAG execution, WebSocket streaming | 2 days | P2 |
| **P4** | Graph builder, entity extraction, relationship linking | 1 day | P3 |
| **P5** | LLM service (Ollama + OpenAI), prompt templates, report formatting | 2 days | P3 |
| **P6** | React UI — dashboard, investigation flow, graph canvas, reports | 4 days | P3, P4, P5 |
| **P7** | Polish, error handling, export (PDF/JSON), auth, deployment | 2 days | P6 |

**Total: ~15 days (full-time)**

---

## 11. Tool Integration Checklist

### Email Intelligence
- [x] **Holehe** — Check email registration on 120+ services — `holehe email@example.com`
- [x] **GHunt** — Google account reconnaissance — `ghunt email email@example.com`
- [x] **h8mail** — Data breach / PGP / paste lookup — `h8mail -t email@example.com`
- [x] **emailfinder** — Domain→email discovery — `emailfinder -d example.com`
- [x] **theHarvester** (email module) — `theHarvester -d example.com -b all`

### Username Intelligence
- [x] **Sherlock** — 400+ social networks — `sherlock username`
- [x] **Maigret** — 2500+ sites (superset of Sherlock) — `maigret username`
- [x] **socid_extractor** — Extract social IDs from profiles
- [ ] **WhatsMyName** — Web extension dataset (can integrate via API)

### Social Media
- [x] **Instaloader** — Instagram profiles, posts, followers — `instaloader profile username`
- [x] **facebook-scraper** — Facebook profiles, posts, friends
- [x] **snscrape** — Twitter/X, Reddit, Telegram, etc.
- [ ] **Twint** (deprecated) → Use snscrape for Twitter

### Domain / Infrastructure
- [x] **theHarvester** (domain module) — subdomains, emails, hosts
- [x] **Censys** — SSL certs, open ports, services
- [x] **Shodan** — IoT, services, vulnerabilities
- [x] **waybackpy** — Wayback Machine historical snapshots
- [x] **restfulHarvest** — API-based subdomain discovery

### Data Breach
- [x] **h8mail** — Breach compilation lookup, paste search
- [x] **holehe** (partial — shows if email exists on services)
- [ ] **Dehashed** (API, paid) — Optional upgrade path

### Utilities
- [x] **tldextract** — Domain parsing
- [x] **Playwright** — Browser automation for JS-heavy sites
- [x] **requests-html** — JavaScript-rendered page scraping

### LLM
- [ ] **Ollama** — `ollama pull llama3.1:8b` (need to install)
- [x] **OpenAI Python SDK** — `pip install openai` (already installed)
- [ ] **LangChain** — Optional for advanced chain-of-thought pipelines

---

## 12. Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Tool CLI changes after update | Pin tool versions in Docker, wrap with integration tests |
| Long-running investigations block requests | Use async subprocess + WebSocket streaming; Celery for heavy jobs |
| Rate limiting / IP bans | Proxy rotation (Tor, SOCKS5), per-tool rate limiter |
| LLM hallucinations in reports | Prompt engineering + source citations; human-review flag |
| Tool installation drift | Docker Compose with pinned tool versions |
| Privacy / data storage | Encrypt results at rest; user-owned data; local-first architecture |

---

## 13. Extensibility

### Adding a New Tool

```python
# 1. Create backend/app/tools/my_new_tool.py
class MyNewTool(BaseTool):
    name = "my_new_tool"
    category = ToolCategory.EMAIL

    async def run(self, target: str, **kwargs) -> ToolResult:
        ...

# 2. Register in backend/app/tools/__init__.py
TOOL_REGISTRY.append(MyNewTool())

# 3. Frontend auto-picks it up via /api/tools endpoint
```

### Future Enhancements

- **Scheduled investigations** — Cron-like recurring scans
- **Team collaboration** — Shared investigations, comments, notes
- **Alerting** — Webhook / email when new findings appear
- **Export plugins** — PDF, CSV, STIX/TAXII for threat intel sharing
- **Plugin marketplace** — Community-contributed tool adapters
- **Dark web monitoring** — Tor + Ahmia / Recon on .onion sites

---

## 14. Quickstart (In-Repo Scripts)

| Script | Purpose |
|--------|---------|
| `scripts/check_tools.py` | Verify all OSINT tools are installed and working |
| `scripts/seed_db.py` | Populate DB with sample investigation data |
| `scripts/test_pipeline.py` | Run end-to-end pipeline on a test email |
| `scripts/backup.sh` | Export all investigations to JSON archive |

```python
# scripts/check_tools.py — Run this first to validate your environment

import subprocess
import sys

TOOLS = {
    "theHarvester": ["theHarvester", "-h"],
    "sherlock": ["sherlock", "--help"],
    "holehe": ["holehe", "--help"],
    "maigret": ["maigret", "--help"],
    "ghunt": ["ghunt", "--help"],
    "h8mail": ["h8mail", "--help"],
    "instaloader": ["instaloader", "--help"],
    "snscrape": ["snscrape", "--help"],
    "censys": ["censys", "--help"],
    "shodan": ["shodan", "--help"],
}

all_ok = True
for name, cmd in TOOLS.items():
    try:
        subprocess.run(cmd, capture_output=True, timeout=10)
        print(f"  ✅ {name}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"  ❌ {name} — NOT FOUND")
        all_ok = False

if all_ok:
    print("\n🎯 All tools are ready!")
else:
    print("\n⚠️  Some tools are missing. Install them before proceeding.")
    sys.exit(1)
```

---

## Final Notes

This plan is **pragmatic, not academic**. Every phase reuses battle-tested OSINT tools — we're not rewriting them, we're orchestrating them under one beautiful hood. The LLM layer turns noise into narrative. The React frontend makes it feel like a product, not a terminal.

**Start with Phase 1 → Phase 2 → Phase 3.** Graph and LLM layers can be built in parallel once the tool adapters are stable. Frontend can start as soon as the API contracts are defined (Pydantic schemas).
