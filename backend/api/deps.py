"""
backend/api/deps.py
Shared authentication and authorization dependency helpers.
All API routes should import from here — never copy-paste auth logic.
"""
from fastapi import HTTPException, Request
from core.auth import get_active_session


def require_session(request: Request) -> dict:
    """
    Require any authenticated, active session.
    Returns the session dict. Raises 401 if missing/invalid.
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session


def require_admin(request: Request) -> dict:
    """
    Require an authenticated Admin session.
    Returns the session dict. Raises 401/403 as appropriate.
    """
    session = require_session(request)
    # role is normalized to lowercase by get_active_session
    if session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return session


def get_session_or_none(request: Request):
    """
    Returns the session dict if a valid session cookie exists, otherwise None.
    Does NOT raise -- use for optional auth endpoints.
    """
    token = request.cookies.get("session_token")
    if not token:
        return None
    return get_active_session(token)
