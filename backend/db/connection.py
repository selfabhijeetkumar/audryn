"""
AUDRYN Database Connection and Lifecycle Management.
SQLite with WAL mode, foreign keys, and connection pooling.
"""
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator, Optional

DEFAULT_DB_PATH = os.path.join("data", "db", "audryn.db")


class DatabaseManager:
    """Manages thread-safe SQLite connections with WAL mode and PRAGMA settings."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("AUDRYN_DB_PATH", DEFAULT_DB_PATH)
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        conn = sqlite3.connect(
            self.db_path,
            timeout=10.0,
            check_same_thread=False,
            isolation_level=None,  # Explicit transaction control
        )
        conn.row_factory = sqlite3.Row
        with conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager providing an atomic transaction."""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            yield conn
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()


db_manager = DatabaseManager()
