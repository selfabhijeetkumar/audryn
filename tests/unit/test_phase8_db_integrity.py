"""
Phase 8 Database Integrity Test Suite — AUDRYN V2.1
Tests: schema presence, WAL mode, FK enforcement, unique constraints,
       decimal precision, SHA-256, SQLite backup/restore.
"""

import os
import io
import hashlib
import sqlite3
import tempfile
import json
import uuid
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.db.connection import DatabaseManager
from backend.db.migrate import run_migrations


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "db", "audryn.db"
)


@pytest.fixture(scope="module")
def db_manager():
    """Provide a DatabaseManager pointing at the production DB for integrity checks."""
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Production DB not found at {DB_PATH}")
    return DatabaseManager(DB_PATH)


@pytest.fixture(scope="function")
def isolated_db(tmp_path):
    """Create an isolated SQLite DB and apply migrations."""
    test_db_path = str(tmp_path / "test_integrity.db")
    run_migrations(test_db_path)
    return test_db_path  # Return path, create DatabaseManager in each test


# ---------------------------------------------------------------------------
# 1. Schema Integrity
# ---------------------------------------------------------------------------

class TestSchemaIntegrity:
    REQUIRED_TABLES = [
        "users", "sessions", "engagements", "engagement_members",
        "evidence_records", "evidence_validity_decisions", "not_checked_items",
        "investigation_jobs", "findings", "counter_evidence_challenges",
        "human_reviews", "calculation_records", "audit_reports",
        "audit_events", "schema_migrations",
    ]

    def test_all_required_tables_exist(self, isolated_db):
        conn = sqlite3.connect(isolated_db)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            existing = {row[0] for row in cursor.fetchall()}
        finally:
            conn.close()

        missing = set(self.REQUIRED_TABLES) - existing
        assert not missing, f"Missing tables after migration: {missing}"

    def test_schema_migrations_table_has_entry(self, isolated_db):
        conn = sqlite3.connect(isolated_db)
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM schema_migrations")
            count = cursor.fetchone()[0]
        finally:
            conn.close()
        assert count >= 1, "No migration entries recorded"

    def test_wal_mode_enabled(self, db_manager):
        conn = db_manager.get_connection()
        try:
            cursor = conn.execute("PRAGMA journal_mode")
            mode = cursor.fetchone()[0]
        finally:
            conn.close()
        assert mode.upper() == "WAL", f"Expected WAL mode, got {mode}"

    def test_foreign_keys_enabled(self, isolated_db):
        mgr = DatabaseManager(isolated_db)
        conn = mgr.get_connection()
        try:
            cursor = conn.execute("PRAGMA foreign_keys")
            enabled = cursor.fetchone()[0]
        finally:
            conn.close()
        assert enabled == 1, "Foreign key enforcement not enabled"


# ---------------------------------------------------------------------------
# 2. Unique Constraint Enforcement
# ---------------------------------------------------------------------------

class TestUniqueConstraints:
    def test_duplicate_username_rejected(self, isolated_db):
        """Inserting two users with the same username must raise an error."""
        conn = sqlite3.connect(isolated_db)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            conn.execute(
                "INSERT INTO users (user_id, username, email, full_name, role, password_hash, salt, is_active, failed_attempts) "
                "VALUES (?, 'dup_user', 'dup@test.com', 'Dup User', 'Associate', 'hash1', 'salt1', 1, 0)",
                (str(uuid.uuid4()),)
            )
            conn.commit()
            with pytest.raises(Exception) as exc_info:
                conn.execute(
                    "INSERT INTO users (user_id, username, email, full_name, role, password_hash, salt, is_active, failed_attempts) "
                    "VALUES (?, 'dup_user', 'dup2@test.com', 'Dup User 2', 'Associate', 'hash2', 'salt2', 1, 0)",
                    (str(uuid.uuid4()),)
                )
                conn.commit()
            assert "unique" in str(exc_info.value).lower()
        finally:
            conn.close()

    def test_duplicate_evidence_hash_allowed_at_db_level(self, isolated_db):
        """Two evidence records with identical SHA-256 — DB allows, app layer should warn."""
        conn = sqlite3.connect(isolated_db)
        try:
            sha256 = "a" * 64
            # Insert engagement first — schema requires entity_name, cin, fiscal_year, assessment_year
            conn.execute(
                "INSERT INTO engagements (engagement_id, entity_name, cin, fiscal_year, assessment_year, currency, status) "
                "VALUES ('ENG-TEST-01', 'Test Corp', 'L12345MH2020PLC000001', 'FY2024', 'AY2025', 'INR', 'ACTIVE')"
            )
            conn.execute(
                "INSERT INTO evidence_records "
                "(evidence_id, engagement_id, original_filename, sha256_hash, file_size_bytes, document_type, extraction_status, raw_storage_path, uploaded_by, page_count) "
                "VALUES (?, 'ENG-TEST-01', 'doc1.pdf', ?, 1024, 'INVOICE', 'EXTRACTED', '/tmp/d1', 'admin', 1)",
                (str(uuid.uuid4()), sha256)
            )
            conn.execute(
                "INSERT INTO evidence_records "
                "(evidence_id, engagement_id, original_filename, sha256_hash, file_size_bytes, document_type, extraction_status, raw_storage_path, uploaded_by, page_count) "
                "VALUES (?, 'ENG-TEST-01', 'doc2.pdf', ?, 2048, 'INVOICE', 'EXTRACTED', '/tmp/d2', 'admin', 1)",
                (str(uuid.uuid4()), sha256)
            )
            conn.commit()
            cursor = conn.execute(
                "SELECT COUNT(*) FROM evidence_records WHERE sha256_hash = ?", (sha256,)
            )
            count = cursor.fetchone()[0]
            assert count == 2, "DB should allow duplicate hashes (application layer handles dedup)"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 3. Transaction Rollback
# ---------------------------------------------------------------------------

class TestTransactionRollback:
    def test_rollback_on_constraint_violation(self, isolated_db):
        """A transaction violating a constraint should not persist partial changes."""
        conn = sqlite3.connect(isolated_db)
        try:
            # Count users before
            count_before = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

            try:
                conn.execute("BEGIN;")
                conn.execute(
                    "INSERT INTO users (user_id, username, email, full_name, role, password_hash, salt, is_active, failed_attempts) "
                    "VALUES (?, 'txn_test_1', 'txn@test.com', 'TxnUser', 'Associate', 'hash', 'salt', 1, 0)",
                    (str(uuid.uuid4()),)
                )
                # Second insert with duplicate username
                conn.execute(
                    "INSERT INTO users (user_id, username, email, full_name, role, password_hash, salt, is_active, failed_attempts) "
                    "VALUES (?, 'txn_test_1', 'txn2@test.com', 'TxnUser2', 'Associate', 'hash', 'salt', 1, 0)",
                    (str(uuid.uuid4()),)
                )
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")

            count_after = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            assert count_after == count_before, "Transaction should have been rolled back entirely"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 4. Decimal Precision Preservation
# ---------------------------------------------------------------------------

class TestDecimalPrecision:
    def test_monetary_decimal_stored_and_retrieved_accurately(self, isolated_db):
        """INR amounts stored as JSON in TEXT columns must round-trip exactly."""
        conn = sqlite3.connect(isolated_db)
        try:
            precise_amount = "1234567890.99"
            calc_id = str(uuid.uuid4())

            # Schema: engagement_id, entity_name, cin, fiscal_year, assessment_year, currency, status
            conn.execute(
                "INSERT INTO engagements (engagement_id, entity_name, cin, fiscal_year, assessment_year, currency, status) "
                "VALUES ('ENG-DEC-01', 'Decimal Test', 'L12345MH2020PLC000002', 'FY2024', 'AY2025', 'INR', 'ACTIVE')"
            )
            # Schema: calculation_id, engagement_id, calculation_name, statutory_section, method, input_values_json, result, ...
            result_text = json.dumps({"net_tax_liability": precise_amount})
            conn.execute(
                "INSERT INTO calculation_records "
                "(calculation_id, engagement_id, calculation_name, method, input_values_json, result) "
                "VALUES (?, 'ENG-DEC-01', 'Tax Liability', 'SECTION_115BAA', '{}', ?)",
                (calc_id, result_text)
            )
            conn.commit()
            cursor = conn.execute(
                "SELECT result FROM calculation_records WHERE calculation_id = ?", (calc_id,)
            )
            row = cursor.fetchone()
            result = json.loads(row[0])
            assert result["net_tax_liability"] == precise_amount, (
                f"Decimal lost precision: stored {precise_amount}, got {result['net_tax_liability']}"
            )
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 5. SHA-256 Verification
# ---------------------------------------------------------------------------

class TestSha256Verification:
    def test_sha256_calculation_correctness(self):
        content = b"AUDRYN Evidence Test Content"
        expected = hashlib.sha256(content).hexdigest()
        calculated = hashlib.sha256(content).hexdigest()
        assert calculated == expected
        assert len(calculated) == 64

    def test_sha256_different_files_differ(self):
        hash1 = hashlib.sha256(b"File content one").hexdigest()
        hash2 = hashlib.sha256(b"File content two").hexdigest()
        assert hash1 != hash2

    def test_sha256_identical_files_match(self):
        content = b"Identical content"
        assert hashlib.sha256(content).hexdigest() == hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
# 6. SQLite Backup / Restore
# ---------------------------------------------------------------------------

class TestSqliteBackupRestore:
    def test_backup_creates_readable_copy(self, tmp_path):
        if not os.path.exists(DB_PATH):
            pytest.skip(f"Production DB not found at {DB_PATH}")

        backup_path = str(tmp_path / "backup_test.db")
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()

        assert os.path.exists(backup_path)
        assert os.path.getsize(backup_path) > 0

        backup_conn = sqlite3.connect(backup_path)
        count = backup_conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        backup_conn.close()
        assert count >= 1

    def test_backup_preserves_user_records(self, tmp_path):
        if not os.path.exists(DB_PATH):
            pytest.skip(f"Production DB not found at {DB_PATH}")

        backup_path = str(tmp_path / "backup_users.db")
        source = sqlite3.connect(DB_PATH)
        source_count = source.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()

        backup_conn = sqlite3.connect(backup_path)
        backup_count = backup_conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        backup_conn.close()
        assert backup_count == source_count
