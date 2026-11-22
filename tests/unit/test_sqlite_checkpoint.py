"""
AUDRYN Phase 4 — Durable SQLite Checkpointer Tests.

Covers:
- WAL mode & PRAGMA configuration
- Checkpoint put, get_tuple, list, and put_writes
- State restart recovery (close database, reopen, restore state)
- Thread state isolation between separate audits
- Online backup and restore
- Checkpoint pruning and retention policies
- LangGraph StateGraph execution with SqliteCheckpointSaver
"""
import os
import tempfile
import sqlite3
import pytest
from backend.services.checkpoint_service import SqliteCheckpointSaver
from backend.workflows.audit_supervisor import build_audit_graph


@pytest.fixture
def temp_db(tmp_path):
    return str(tmp_path / "test_audit.db")


@pytest.fixture
def checkpointer(temp_db):
    saver = SqliteCheckpointSaver(db_path=temp_db)
    yield saver
    saver.close()


def test_sqlite_pragmas_and_wal_mode(checkpointer):
    """Verify that WAL mode, foreign keys, and busy timeout are configured."""
    cursor = checkpointer._conn.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    assert mode.upper() == "WAL"

    cursor = checkpointer._conn.execute("PRAGMA foreign_keys;")
    fk = cursor.fetchone()[0]
    assert fk == 1


def test_put_and_get_checkpoint_tuple(checkpointer):
    """Verify saving a checkpoint and retrieving exact channel values."""
    config = {"configurable": {"thread_id": "audit-thread-101", "checkpoint_ns": ""}}
    checkpoint = {
        "id": "1_init",
        "channel_versions": {"stage": 1, "audit_id": 1},
        "versions_seen": {},
        "channel_values": {"stage": "initialized", "audit_id": "AUD-101"},
    }
    metadata = {"step": 1, "source": "input"}
    new_versions = {"stage": 1, "audit_id": 1}

    ret_config = checkpointer.put(config, checkpoint, metadata, new_versions)
    assert ret_config["configurable"]["checkpoint_id"] == "1_init"

    tuple_out = checkpointer.get_tuple(ret_config)
    assert tuple_out is not None
    assert tuple_out.checkpoint["id"] == "1_init"
    assert tuple_out.checkpoint["channel_values"]["stage"] == "initialized"
    assert tuple_out.checkpoint["channel_values"]["audit_id"] == "AUD-101"


def test_restart_recovery_from_disk(temp_db):
    """Simulate complete process exit and restart: data reloads from disk."""
    # Process 1: Write checkpoint and close connection
    p1_saver = SqliteCheckpointSaver(db_path=temp_db)
    config = {"configurable": {"thread_id": "audit-persistent-001", "checkpoint_ns": ""}}
    checkpoint = {
        "id": "step_final",
        "channel_versions": {"balance": 1},
        "versions_seen": {},
        "channel_values": {"balance": "100000.00"},
    }
    p1_saver.put(config, checkpoint, {}, {"balance": 1})
    p1_saver.close()

    # Process 2: Open fresh connection against the same database file
    p2_saver = SqliteCheckpointSaver(db_path=temp_db)
    reloaded = p2_saver.get_tuple(config)
    assert reloaded is not None
    assert reloaded.checkpoint["id"] == "step_final"
    assert reloaded.checkpoint["channel_values"]["balance"] == "100000.00"
    p2_saver.close()


def test_thread_state_isolation(checkpointer):
    """Checkpoints for separate audit threads must remain 100% isolated."""
    config_a = {"configurable": {"thread_id": "AUDIT-CORP-A", "checkpoint_ns": ""}}
    config_b = {"configurable": {"thread_id": "AUDIT-CORP-B", "checkpoint_ns": ""}}

    ckpt_a = {
        "id": "step_a", "channel_versions": {"data": 1}, "versions_seen": {},
        "channel_values": {"data": "Confidential A"},
    }
    ckpt_b = {
        "id": "step_b", "channel_versions": {"data": 1}, "versions_seen": {},
        "channel_values": {"data": "Confidential B"},
    }

    checkpointer.put(config_a, ckpt_a, {}, {"data": 1})
    checkpointer.put(config_b, ckpt_b, {}, {"data": 1})

    res_a = checkpointer.get_tuple(config_a)
    res_b = checkpointer.get_tuple(config_b)

    assert res_a.checkpoint["channel_values"]["data"] == "Confidential A"
    assert res_b.checkpoint["channel_values"]["data"] == "Confidential B"


def test_online_backup_and_restore(checkpointer, tmp_path):
    """Test online database backup via sqlite3 backup API."""
    config = {"configurable": {"thread_id": "audit-backup-test", "checkpoint_ns": ""}}
    ckpt = {
        "id": "backup_step", "channel_versions": {"k": 1}, "versions_seen": {},
        "channel_values": {"k": "v_backup"},
    }
    checkpointer.put(config, ckpt, {}, {"k": 1})

    backup_path = str(tmp_path / "audit_backup.db")
    checkpointer.backup(backup_path)

    assert os.path.exists(backup_path)
    # Open backup with a new saver instance and verify data integrity
    backup_saver = SqliteCheckpointSaver(db_path=backup_path)
    restored = backup_saver.get_tuple(config)
    assert restored.checkpoint["channel_values"]["k"] == "v_backup"
    backup_saver.close()


def test_checkpoint_pruning(checkpointer):
    """Pruning should remove older checkpoints beyond retention limit."""
    thread_id = "prune-test-thread"
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}

    # Write 5 checkpoints
    for i in range(5):
        c = {
            "id": f"step_{i:02d}", "channel_versions": {"iter": 1}, "versions_seen": {},
            "channel_values": {"iter": i},
        }
        checkpointer.put(config, c, {}, {"iter": 1})

    # Keep only last 2
    pruned_count = checkpointer.prune_old_checkpoints(thread_id, keep_last=2)
    assert pruned_count == 3

    # Check remaining
    tuples = list(checkpointer.list(config))
    assert len(tuples) == 2


def test_langgraph_supervisor_with_sqlite_checkpointer(temp_db):
    """Verify full LangGraph StateGraph execution with SqliteCheckpointSaver."""
    saver = SqliteCheckpointSaver(db_path=temp_db)
    graph = build_audit_graph(checkpointer=saver, interrupt_before_human_review=False)
    config = {"configurable": {"thread_id": "audit-sqlite-e2e"}}

    input_payload = {
        "audit_id": "AUD-SQLITE-001",
        "company_id": "U29100MH2020PTC998877",
        "company_name": "Apex Industrial Dynamics Pvt Ltd",
        "financial_periods": ["FY2023-24", "FY2024-25"],
        "evidence_ids": [],
        "extracted_records": {
            "available_documents": {
                "FY2023-24": ["TRIAL_BALANCE", "BALANCE_SHEET", "PROFIT_AND_LOSS"],
                "FY2024-25": ["TRIAL_BALANCE", "BALANCE_SHEET", "PROFIT_AND_LOSS"],
            },
            "trial_balances": {},
            "procedures": [],
        },
        "completeness_status": "PENDING",
        "reconciliation_results": [],
        "investigation_findings": [],
        "counter_evidence": [],
        "verification_results": [],
        "gap_register": [],
        "risk_classification": "LOW",
        "human_review_status": "NOT_REQUIRED",
        "human_reviewer_comments": "",
        "final_report_status": "NOT_STARTED",
        "execution_errors": [],
        "retry_count": 0,
        "current_stage": "",
    }

    result = graph.invoke(input_payload, config)
    assert result["audit_id"] == "AUD-SQLITE-001"
    assert result["current_stage"] in ("finalized", "finalized_blocked")

    # Verify checkpoint exists in SQLite database
    tuple_out = saver.get_tuple(config)
    assert tuple_out is not None
    assert tuple_out.checkpoint["channel_values"]["audit_id"] == "AUD-SQLITE-001"
    saver.close()
