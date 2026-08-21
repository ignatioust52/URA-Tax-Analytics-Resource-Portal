from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend.api.resources import serialize_df
from core.db_users import users_get_all, users_toggle_active
from backend.api.deps import require_admin

router = APIRouter()

class StatusRequest(BaseModel):
    user_id: int
    is_active: bool
    status: str

@router.get("/")
def get_users(request: Request):
    require_admin(request)
    df = users_get_all()
    if df.empty:
        return []
    return serialize_df(df)

@router.post("/status")
def update_status(req: StatusRequest, request: Request):
    session = require_admin(request)
    admin_id = session.get("id")
    
    # Prevent self-disable
    if req.user_id == admin_id and not req.is_active:
        raise HTTPException(status_code=400, detail="Cannot disable your own admin account")
        
    users_toggle_active(req.user_id)
    return {"success": True, "message": "User status updated"}

@router.get("/pending")
def get_pending_users(request: Request):
    require_admin(request)
    from core.db_users import users_get_pending
    df = users_get_pending()
    if df.empty:
        return []
    return serialize_df(df)

class ApproveRequest(BaseModel):
    user_id: int
    role: str
    department_ids: list[int]

@router.post("/approve")
def approve_user(req: ApproveRequest, request: Request):
    require_admin(request)
    from core.db_users import users_approve
    try:
        users_approve(req.user_id, req.role, req.department_ids)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RejectRequest(BaseModel):
    user_id: int

@router.post("/reject")
def reject_user(req: RejectRequest, request: Request):
    require_admin(request)
    from core.db_users import users_reject
    try:
        users_reject(req.user_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str
    department_ids: list[int]

@router.post("/create")
def create_user(req: CreateUserRequest, request: Request):
    require_admin(request)
    from core.db_users import users_create
    from core.auth import is_password_strong
    
    ok, msg = is_password_strong(req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
        
    try:
        users_create(req.email.lower().strip(), req.password, req.role, req.department_ids)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
def get_sessions(request: Request):
    require_admin(request)
    from core.db import get_connection
    import pandas as pd
    
    conn = get_connection()
    query = """
        SELECT us.token, us.user_id, us.last_activity_at, u.email, u.department
        FROM user_sessions us
        JOIN app_users u ON u.id = us.user_id
        ORDER BY us.last_activity_at DESC
    """
    df = pd.read_sql(query, conn)
    # Convert timestamps to string
    if not df.empty:
        df["last_activity_at"] = df["last_activity_at"].astype(str)
    return serialize_df(df)

@router.delete("/sessions/{token}")
def revoke_session(token: str, request: Request):
    require_admin(request)
    from core.auth import delete_user_session
    try:
        delete_user_session(token)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
