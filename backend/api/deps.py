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


def require_permission(permission_key: str):
    """
    Dependency factory to require a specific permission.
    Usage: Depends(require_permission("view_dashboard"))
    """
    def _require_permission(request: Request) -> dict:
        session = require_session(request)
        from core.auth import has_permission
        if not has_permission(session["id"], permission_key):
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission_key}")
        return session
    return _require_permission


def require_admin(request: Request) -> dict:
    """
    Legacy wrapper - transitions to requiring 'manage_system_settings' or 'approve_users'
    depending on context, but for now we'll map it to 'manage_system_settings'
    to represent core admin access.
    """
    session = require_session(request)
    from core.auth import has_permission
    if not has_permission(session["id"], "manage_system_settings"):
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
    from core.auth import get_active_session
    return get_active_session(token)
