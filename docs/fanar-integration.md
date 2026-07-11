# Fanar LLM Integration

## Overview

Meower uses **Fanar API** for all LLM-powered features (report generation, analysis, summarization). Fanar is fully **OpenAI-compatible**, so we use the OpenAI Python SDK with a custom base URL.

- **Base URL:** `https://api.fanar.qa/v1`
- **Auth:** Bearer token (API key)
- **Rate Limit:** 50 req/min (most models)
- **API Docs:** https://api.fanar.qa/docs

## Models

| Model | Use Case | Rate Limit |
|-------|----------|-----------|
| `Fanar` | General-purpose, default | 50 req/min |
| `Fanar-C-2-27B` | Heavy analysis, thinking mode | 50 req/min |
| `Fanar-C-1-8.7B` | Faster, lighter tasks | 50 req/min |
| `Fanar-S-1-7B` | Fast inference | 50 req/min |
| `Fanar-Sadiq` | Islamic content | 50 req/min |
| `Fanar-Diwan` | Poetry & creative | 50 req/min |

## Getting an API Key

1. Visit https://api.fanar.qa/request
2. Request API access
3. Set the key in your environment:
   ```bash
   export FANAR_API_KEY=your-key-here
   ```

## Usage

### Python (via OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-fanar-api-key",
    base_url="https://api.fanar.qa/v1"
)

response = client.chat.completions.create(
    model="Fanar-C-2-27B",
    messages=[
        {"role": "system", "content": "You are an OSINT analyst."},
        {"role": "user", "content": "Summarize these findings..."}
    ],
    temperature=0.3,
    max_tokens=4096
)

print(response.choices[0].message.content)
```

### From the App

Set the env var and the app handles the rest:

```bash
docker run -e FANAR_API_KEY=your-key -p 8000:8000 meower
```

## Configuration

All config is in `backend/app/core/config.py`:

```python
fanar_api_key: str = ""          # Required
fanar_base_url: str = "https://api.fanar.qa/v1"
fanar_model: str = "Fanar-C-2-27B"
fanar_timeout: int = 120
```

## Prompt Template

System prompt for OSINT report generation (in `backend/app/llm/prompts.py`):

```
You are Meower AI, an expert OSINT analyst...
```

## Architecture

```
┌──────────────┐     POST /v1/chat/completions     ┌────────────┐
│  LLM Service  │ ───────────────────────────────▶  │  Fanar API  │
│  (app/llm/)   │ ◀───────────────────────────────  │  (Qatar)    │
└──────────────┘     {choices[0].message.content}   └────────────┘
```

## Fallback / No-Key Mode

If `FANAR_API_KEY` is not set, the `/api/v1/report/generate` endpoint returns an error explaining that the API key is required. No local model is used — everything goes through Fanar's cloud API.
