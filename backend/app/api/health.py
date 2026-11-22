"""
AUDRYN Health and System Status Endpoint.
Reports service status, database health, evidence vault availability, and Ollama connectivity.
"""
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.db.connection import db_manager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def get_health():
    # Database check
    db_ok = False
    try:
        conn = db_manager.get_connection()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT 1;")
            db_ok = cur.fetchone()[0] == 1
        conn.close()
    except Exception:
        db_ok = False

    # Vault check
    vault_path = os.path.join("data", "evidence_vault")
    vault_ok = os.path.exists(vault_path) and os.access(vault_path, os.W_OK)

    # Local Ollama check (timeout 0.5s to avoid blocking)
    ollama_ok = False
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            ollama_ok = resp.status == 200
    except Exception:
        ollama_ok = False

    return {
        "status": "healthy" if db_ok and vault_ok else "degraded",
        "service": "AUDRYN Audit Intelligence System",
        "version": "2.1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database": {"connected": db_ok, "engine": "SQLite WAL"},
        "evidence_vault": {"accessible": vault_ok, "path": vault_path},
        "inference": {"provider": "Ollama (Local)", "connected": ollama_ok, "model": "qwen3:4b"},
    }
