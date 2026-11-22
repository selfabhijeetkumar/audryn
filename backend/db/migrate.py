"""
AUDRYN Database Migration Runner.
Applies versioned SQL migrations atomically to SQLite.
"""
import hashlib
import os
import sqlite3
import sys
from typing import List, Tuple
from backend.db.connection import DatabaseManager, DEFAULT_DB_PATH

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def compute_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def get_migration_files() -> List[Tuple[str, str, str]]:
    """Returns sorted list of (version, filename, full_path)."""
    files = []
    if not os.path.exists(MIGRATIONS_DIR):
        return []
    for fname in sorted(os.listdir(MIGRATIONS_DIR)):
        if fname.endswith(".sql"):
            version = fname.split("_")[0]
            files.append((version, fname, os.path.join(MIGRATIONS_DIR, fname)))
    return files


def run_migrations(db_path: str = DEFAULT_DB_PATH) -> int:
    """Applies all pending migrations. Returns count of applied migrations."""
    mgr = DatabaseManager(db_path)
    conn = mgr.get_connection()
    applied_count = 0

    try:
        # Ensure migrations table exists
        with conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT NOT NULL
            );
            """)

        cur = conn.cursor()
        cur.execute("SELECT version, checksum FROM schema_migrations;")
        applied = {row["version"]: row["checksum"] for row in cur.fetchall()}

        for version, fname, fpath in get_migration_files():
            checksum = compute_file_hash(fpath)
            if version in applied:
                if applied[version] != checksum:
                    raise RuntimeError(
                        f"Migration {fname} checksum mismatch! Expected {applied[version]}, found {checksum}"
                    )
                continue

            print(f"Applying migration: {fname}...")
            with open(fpath, "r", encoding="utf-8") as f:
                sql_content = f.read()

            with conn:
                conn.executescript(sql_content)
                conn.execute(
                    "INSERT INTO schema_migrations (version, description, checksum) VALUES (?, ?, ?);",
                    (version, fname, checksum),
                )
            applied_count += 1
            print(f"Successfully applied: {fname}")

    finally:
        conn.close()

    return applied_count


if __name__ == "__main__":
    target_db = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB_PATH
    count = run_migrations(target_db)
    print(f"Migrations complete. {count} migration(s) applied to {target_db}.")
