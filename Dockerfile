# AUDRYN — Dockerfile
# Evidence-First Multi-Agent Financial Audit Intelligence System
#
# Build:  docker build -t audryn:v2.1 .
# Run:    docker run -p 8000:8000 -v ./data:/app/data audryn:v2.1

FROM python:3.13-slim

LABEL maintainer="AUDRYN Development Team"
LABEL version="2.1"
LABEL description="AUDRYN backend — FastAPI + SQLite WAL"

# Security: run as non-root
RUN groupadd -r audryn && useradd -r -g audryn -m audryn

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn[standard]

# Copy application
COPY backend/ ./backend/
COPY data/ ./data/

# Ensure data directories exist and are writable
RUN mkdir -p data/db data/evidence data/reports logs && \
    chown -R audryn:audryn /app

USER audryn

# Environment defaults
ENV PYTHONPATH=/app
ENV AUDRYN_DB_PATH=data/db/audryn.db
ENV AUDRYN_EVIDENCE_DIR=data/evidence
ENV AUDRYN_SECRET_KEY=CHANGE_ME_IN_PRODUCTION

# Apply migrations on startup, then start server
CMD python -m backend.db.migrate && \
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"
