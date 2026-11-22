"""
AUDRYN Authentication Endpoints.
Login, logout, session verification, and CSRF token provisioning.
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from backend.app.auth import (
    AuthService,
    get_current_user,
    get_current_session_and_user,
    SESSION_COOKIE_NAME,
    CSRF_HEADER_NAME,
)
from backend.app.rbac import ROLE_PERMISSIONS, Role

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    permissions: list[str]


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    user = AuthService.authenticate_user(payload.username, payload.password)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    session_id, csrf_token = AuthService.create_session(
        user["user_id"], ip_address=client_ip, user_agent=user_agent
    )

    # Set httpOnly session cookie
    is_https = request.url.scheme == "https"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=is_https,
        samesite="lax",
        max_age=12 * 3600,  # 12 hours absolute
        path="/",
    )
    response.headers[CSRF_HEADER_NAME] = csrf_token

    user_role = Role(user["role"])
    permissions = [p.value for p in ROLE_PERMISSIONS.get(user_role, set())]

    return {
        "message": "Authentication successful.",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": bool(user["is_active"]),
            "permissions": permissions,
        },
        "csrf_token": csrf_token,
    }


@router.post("/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        AuthService.revoke_session(session_id)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"message": "Successfully logged out. Session invalidated."}


@router.get("/me")
def get_me(user: Dict[str, Any] = Depends(get_current_user), data=Depends(get_current_session_and_user)):
    session, _ = data
    user_role = Role(user["role"])
    permissions = [p.value for p in ROLE_PERMISSIONS.get(user_role, set())]

    return {
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "permissions": permissions,
        },
        "csrf_token": session["csrf_token"],
    }
