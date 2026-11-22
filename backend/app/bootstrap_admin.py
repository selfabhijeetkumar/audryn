"""
AUDRYN Secure Local Administrator Bootstrap Script.
Creates initial Partner or administrative account safely.
"""
import argparse
import sys
from backend.app.auth import AuthService
from backend.app.rbac import Role
from backend.db.connection import db_manager


def bootstrap_admin(username: str, email: str, full_name: str, password: str, role: str = "Partner"):
    conn = db_manager.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE username = ? OR email = ?;", (username, email))
        existing = cur.fetchone()
        if existing:
            print(f"User '{username}' or email '{email}' already exists. Skipping bootstrap.")
            return existing["user_id"]
    finally:
        conn.close()

    user = AuthService.create_user(
        username=username,
        email=email,
        full_name=full_name,
        role=role,
        password=password,
    )
    print(f"Successfully bootstrapped user: {user['username']} ({user['role']}) - ID: {user['user_id']}")
    return user["user_id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap AUDRYN admin user")
    parser.add_argument("--username", default="audryn_partner", help="Username")
    parser.add_argument("--email", default="partner@audryn.local", help="Email")
    parser.add_argument("--name", default="Senior Engagement Partner", help="Full name")
    parser.add_argument("--role", default="Partner", choices=[r.value for r in Role], help="Role")
    parser.add_argument("--password", required=True, help="Password (minimum 8 characters)")

    args = parser.parse_args()
    if len(args.password) < 8:
        print("Error: Password must be at least 8 characters long.", file=sys.stderr)
        sys.exit(1)

    bootstrap_admin(args.username, args.email, args.name, args.password, args.role)
