"""
AUDRYN Authentication and Session Management Service.
Standard-library PBKDF2 password hashing, server-side SQLite sessions,
idle & absolute timeout enforcement, CSRF protection, and rate limiting.
"""
import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, Response, HTTPException, status, Depends
from backend.db.connection import db_manager
from backend.app.rbac import Permission, has_permission, Role

SESSION_COOKIE_NAME = "audryn_session"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Session Durations
IDLE_TIMEOUT_MINUTES = 30
ABSOLUTE_TIMEOUT_HOURS = 12
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> Tuple[str, str]:
    """Hashes password with PBKDF2-HMAC-SHA256 and cryptographic salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifies password using constant-time comparison."""
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return secrets.compare_digest(key.hex(), password_hash)


class AuthService:
    """Authentication and session lifecycle operations."""

    @staticmethod
    def create_user(
        username: str,
        email: str,
        full_name: str,
        role: str,
        password: str,
    ) -> Dict[str, Any]:
        """Creates a new user record with hashed credentials."""
        if role not in [r.value for r in Role]:
            raise ValueError(f"Invalid role '{role}'.")

        pw_hash, salt = hash_password(password)
        user_id = f"USR-{secrets.token_hex(6)}"

        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, email, full_name, role, password_hash, salt, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1);
                """,
                (user_id, username, email, full_name, role, pw_hash, salt),
            )

        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": True,
        }

    @staticmethod
    def authenticate_user(username: str, password: str) -> Dict[str, Any]:
        """Authenticates user with rate limiting and lockout protection."""
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username = ? OR email = ?;", (username, username))
            user = cur.fetchone()

            now = datetime.now(timezone.utc)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials.",
                )

            # Check lockout
            if user["locked_until"]:
                locked_until = datetime.fromisoformat(user["locked_until"])
                if now < locked_until:
                    remaining = int((locked_until - now).total_seconds() / 60)
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Account locked due to multiple failed attempts. Try again in {remaining + 1} minutes.",
                    )

            if not verify_password(password, user["password_hash"], user["salt"]):
                failed = user["failed_attempts"] + 1
                locked_until_str = None
                if failed >= MAX_FAILED_LOGIN_ATTEMPTS:
                    locked_until_str = (now + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()

                with conn:
                    conn.execute(
                        "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE user_id = ?;",
                        (failed, locked_until_str, user["user_id"]),
                    )

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials.",
                )

            # Reset failed attempts on success
            with conn:
                conn.execute(
                    "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE user_id = ?;",
                    (user["user_id"],),
                )

            return dict(user)
        finally:
            conn.close()

    @staticmethod
    def create_session(
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Creates a new session and returns (session_id, csrf_token)."""
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=ABSOLUTE_TIMEOUT_HOURS)).isoformat()
        now_str = now.isoformat()

        with db_manager.session() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, user_id, csrf_token, created_at, expires_at, last_accessed_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (session_id, user_id, csrf_token, now_str, expires_at, now_str, ip_address, user_agent),
            )

        return session_id, csrf_token

    @staticmethod
    def get_session_and_user(session_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Validates session idle and absolute timeouts. Returns (session, user) or None."""
        conn = db_manager.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.*, u.username, u.email, u.full_name, u.role, u.is_active
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.session_id = ?;
                """,
                (session_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            now = datetime.now(timezone.utc)
            expires_at = datetime.fromisoformat(row["expires_at"])
            last_accessed = datetime.fromisoformat(row["last_accessed_at"])

            # Check absolute expiration
            if now > expires_at:
                with conn:
                    conn.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
                return None

            # Check idle expiration
            if now - last_accessed > timedelta(minutes=IDLE_TIMEOUT_MINUTES):
                with conn:
                    conn.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
                return None

            # Update last accessed
            with conn:
                conn.execute(
                    "UPDATE sessions SET last_accessed_at = ? WHERE session_id = ?;",
                    (now.isoformat(), session_id),
                )

            session_data = {
                "session_id": row["session_id"],
                "user_id": row["user_id"],
                "csrf_token": row["csrf_token"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
            }
            user_data = {
                "user_id": row["user_id"],
                "username": row["username"],
                "email": row["email"],
                "full_name": row["full_name"],
                "role": row["role"],
                "is_active": bool(row["is_active"]),
            }
            return session_data, user_data
        finally:
            conn.close()

    @staticmethod
    def revoke_session(session_id: str):
        """Invalidates a session on logout."""
        with db_manager.session() as conn:
            conn.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))


# Dependencies for FastAPI
def get_current_session_and_user(request: Request) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. No session cookie.",
        )
    result = AuthService.get_session_and_user(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please re-authenticate.",
        )
    return result


def get_current_user(data: Tuple[Dict[str, Any], Dict[str, Any]] = Depends(get_current_session_and_user)) -> Dict[str, Any]:
    _, user = data
    if not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account.")
    return user


def verify_csrf(request: Request, data: Tuple[Dict[str, Any], Dict[str, Any]] = Depends(get_current_session_and_user)):
    """Verifies CSRF header for state-changing HTTP operations."""
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        session, _ = data
        header_token = request.headers.get(CSRF_HEADER_NAME)
        if not header_token or not secrets.compare_digest(header_token, session["csrf_token"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed. Missing or invalid X-CSRF-Token header.",
            )


def require_permission(permission: Permission):
    """Enforces specific RBAC permission check on current user."""
    def dependency(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "")
        if not has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{user_role}' lacks permission '{permission.value}'.",
            )
        return user
    return dependency
