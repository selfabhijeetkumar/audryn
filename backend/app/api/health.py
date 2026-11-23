"""
AUDRYN Health and System Status Endpoint.
Reports service status, database health, evidence vault availability, and inference provider readiness.
Decoupled: Service is healthy even when local Ollama is not present in cloud environments.
"""
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from fastapi import APIRouter
from backend.db.connection import db_manager
from backend.providers.config import ProviderConfig

router = APIRouter(prefix="/health", tags=["Health"])


@router.api_route("", methods=["GET", "HEAD"])
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
    vault_path = os.environ.get("AUDRYN_VAULT_PATH", os.path.join("data", "evidence_vault"))
    try:
        os.makedirs(vault_path, exist_ok=True)
    except Exception:
        pass
    vault_ok = os.path.exists(vault_path) and os.access(vault_path, os.W_OK)

    # Local Ollama check (timeout 0.5s to avoid blocking)
    ollama_ok = False
    is_cloud = ProviderConfig.is_cloud_env
    if not is_cloud:
        try:
            req = urllib.request.Request(f"{ProviderConfig.OLLAMA_BASE_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                ollama_ok = resp.status == 200
        except Exception:
            ollama_ok = False

    priority_chain = ProviderConfig.get_priority_chain()
    primary_provider = priority_chain[0] if priority_chain else "none"

    return {
        "status": "healthy" if db_ok and vault_ok else "degraded",
        "service": "AUDRYN Audit Intelligence System",
        "version": "2.1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database": {"connected": db_ok, "engine": "SQLite WAL"},
        "evidence_vault": {"accessible": vault_ok, "path": vault_path},
        "inference": {
            "mode": ProviderConfig.MODE,
            "primary_provider": primary_provider,
            "local_ollama_connected": ollama_ok,
            "cloud_failover_enabled": True,
            "deterministic_arithmetic_engine": "READY",
        },
    }
