# AUDRYN — Durable Persistence Architecture

> **Document Type:** System Architecture Specification  
> **Component:** Checkpoint Persistence & State Durability  
> **Module:** `backend/services/checkpoint_service.py`  
> **Status:** ACTIVE & PRODUCTION-GRADE  
> **Zero External Binaries:** Pure Python Standard Library `sqlite3`

---

## 1. Architectural Motivation

In high-stakes statutory financial audits, state loss during an multi-agent investigation is unacceptable. An audit execution involving hundreds of document tie-outs, ledger reconciliations, cross-year comparisons, and counter-evidence queries can take minutes to hours.

AUDRYN implements **`SqliteCheckpointSaver`**, a custom production-grade checkpointer derived from LangGraph's `BaseCheckpointSaver`. It replaces in-memory checkpointers with an ACID-compliant, disk-backed relational persistence layer.

### Core Architectural Guarantees:
1. **Zero External Native Binaries:** Built exclusively on Python 3.13 standard library `sqlite3`, ensuring 100% compliance with Windows Application Control (AppLocker/WDAC).
2. **ACID Transactional Integrity:** Every graph node transition and channel write is captured in atomic SQLite transactions.
3. **Multi-Thread Safety:** LangGraph Pregel runs background worker threads concurrently. A dedicated `threading.Lock()` mutex coordinates SQLite operations, completely preventing `SQLITE_MISUSE` and connection corruption.
4. **Thread Isolation (Multi-Tenancy):** Each audit engagement maps 1:1 to a unique `thread_id` (`AUD-YYYY-NNN`). State, channel versions, and pending writes are partitioned strictly by `(thread_id, checkpoint_ns)`.
5. **Zero Document Payload Bloat:** Large document payloads (e.g. 50 MB PDFs) reside in the SHA-256 Evidence Vault on disk. Only evidence UUID pointers, cryptographic hashes, and structured calculation records are serialized into checkpoints.

---

## 2. Database Schema & Indexing

The checkpointer creates and manages three relational tables and dedicated performance indexes:

```sql
-- Main checkpoint container storing graph snapshot metadata
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    checkpoint_type TEXT NOT NULL,
    checkpoint_data BLOB NOT NULL,
    metadata_type TEXT NOT NULL,
    metadata_data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- Normalized channel blobs storing individual channel values by version
CREATE TABLE IF NOT EXISTS checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL,
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    blob_type TEXT NOT NULL,
    blob_data BLOB NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);

-- Intermediate pending writes captured during interrupted or multi-task steps
CREATE TABLE IF NOT EXISTS checkpoint_writes (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    idx INTEGER NOT NULL,
    channel TEXT NOT NULL,
    write_type TEXT NOT NULL,
    write_data BLOB NOT NULL,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);

-- Fast chronologically ordered listing for time-travel & pruning
CREATE INDEX IF NOT EXISTS idx_checkpoints_created 
ON checkpoints(thread_id, checkpoint_ns, created_at);
```

---

## 3. SQLite Concurrency & PRAGMA Settings

To prevent database contention under concurrent multi-agent executions, `SqliteCheckpointSaver` automatically executes the following PRAGMAs on connection initialization:

```sql
PRAGMA journal_mode = WAL;         -- Write-Ahead Logging enables non-blocking readers
PRAGMA synchronous = NORMAL;       -- Safe crash-resilient write performance in WAL mode
PRAGMA foreign_keys = ON;          -- Strict referential integrity enforcement
PRAGMA busy_timeout = 5000;        -- 5000ms automatic retry on file locks before error
```

### 3.1 WAL Mode (Write-Ahead Logging) Mechanics
- **Concurrent Execution:** Multiple read transactions operate concurrently with a single write transaction without blocking.
- **Atomic Commits:** Changes are written to the `-wal` file sequentially; readers view a consistent point-in-time snapshot.
- **Crash Recovery:** If a crash or power failure occurs, SQLite reconstructs the exact state from the WAL file on reopening.

---

## 4. Multi-Threading & Thread Safety Architecture

LangGraph's execution engine (`SyncPregelLoop`) utilizes `concurrent.futures.ThreadPoolExecutor` to dispatch parallel node computations (such as parallel specialist agent tasks).

### 4.1 The SQLite Multi-Threading Challenge
Even when `sqlite3.connect(..., check_same_thread=False)` is specified, the underlying C-level `sqlite3*` handle is not safe for simultaneous reentrant operations across threads. Concurrent execution of `INSERT` or `SELECT` without synchronization produces `sqlite3.InterfaceError: bad parameter or other API misuse` (`SQLITE_MISUSE`).

### 4.2 AUDRYN Mutex Architecture
AUDRYN resolves this cleanly by wrapping every connection access in a reentrant-safe thread lock:

```python
class SqliteCheckpointSaver(BaseCheckpointSaver):
    def __init__(self, ...):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(...)
        ...

    def put(self, config, checkpoint, metadata, new_versions):
        ...
        with self._lock, self._conn:
            # Atomic database execution across threads
            ...
```

---

## 5. Lifecycle Operations & Maintenance

### 5.1 Restart Recovery
When an audit session is terminated or the application process exits, state is preserved on disk:
1. On startup, `SqliteCheckpointSaver(db_path=...)` opens the existing database file.
2. Invoking `saver.get_tuple(config)` retrieves the exact channel versions, reconstructed state dictionaries, and pending writes.
3. The supervisor graph can resume execution from the exact interrupted node.

### 5.2 Thread State Isolation
Each audit engagement has a dedicated `thread_id`:
- Audit A (`thread_id="AUD-2024-001"`) cannot read, overwrite, or access Audit B (`thread_id="AUD-2024-002"`).
- Queries strictly scope by `WHERE thread_id = ? AND checkpoint_ns = ?`.

### 5.3 Live Online Backups
Live snapshots of active audits can be created without taking the database offline or blocking write transactions:
```python
saver.backup("backups/audit_snapshot_20261122.db")
```
This utilizes `self._conn.backup(dest_conn)` to perform a zero-downtime, page-by-page transaction-consistent backup.

### 5.4 Checkpoint Retention & Pruning
Long-running audits generate dozens of intermediate state steps. `prune_old_checkpoints(thread_id, keep_last=10)` removes historical checkpoint snapshots exceeding the specified retention threshold while preserving the latest states and foreign key consistency.
