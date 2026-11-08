# syntax=docker/dockerfile:1
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS python-deps
ENV PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    SCHEDULER_ENABLED=false
WORKDIR /app
COPY --from=python-deps /install /usr/local
COPY backend/ ./backend/
COPY config/ ./config/
COPY data/processed/rag_chunks.json ./data/processed/rag_chunks.json
COPY --from=frontend-build /build/frontend/dist ./frontend/dist
RUN groupadd --system app && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/data/private \
    && chown -R app:app /app/data
USER app
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --proxy-headers"]
