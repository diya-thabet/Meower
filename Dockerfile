# ---- Stage 1: Build frontend ----
FROM node:22-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ---- Stage 2: Python backend ----
FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uvicorn

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

COPY --from=frontend-builder /build/frontend/dist /app/frontend/dist

RUN mkdir -p /app/data

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV FRONTEND_DIR=/app/frontend/dist
ENV DATABASE_URL=sqlite+aiosqlite:///./data/meower.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
