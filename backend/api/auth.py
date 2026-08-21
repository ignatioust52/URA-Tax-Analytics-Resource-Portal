from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
import bcrypt
import pandas as pd
from core.db import get_connection
from core.auth import user_get_by_email, create_user_session, get_active_session, delete_user_session

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login(login_req: LoginRequest, response: Response):
    user = user_get_by_email(login_req.email)
    if user is None or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Invalid credentials or account disabled")
    
    # Hash check
    if not bcrypt.checkpw(login_req.password.encode('utf-8'), str(user["password_hash"]).encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    session_token = create_user_session(user["id"])
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="session_token", 
        value=session_token, 
        httponly=True, 
        samesite="lax",
        max_age=3600
    )
    
    return {
        "success": True, 
        "user": {
            "email": user["email"],
            "role": str(user.get("role_name") or user.get("role") or "").lower(),
            "department": user["department"]
        }
    }

@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        delete_user_session(token)
    response.delete_cookie("session_token")
    return {"success": True}

@router.get("/me")
def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Return a clean, frontend-friendly payload with canonical lowercase role.
    return {
        "id": session.get("id"),
        "user_id": session.get("id"),
        "email": session.get("email"),
        "role": session.get("role"),        # always lowercase: 'admin' | 'viewer'
        "role_name": session.get("role_name"),  # original casing from roles table
        "department": session.get("department"),
    }

class RegisterRequest(BaseModel):
    email: str
    password: str
    confirm_password: str
    department: str

@router.post("/register")
def register(req: RegisterRequest):
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
        
    from core.auth import is_password_strong
    ok, msg = is_password_strong(req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
        
    from core.db_users import users_register
    try:
        users_register(req.email.lower().strip(), req.password, req.department)
        return {"success": True, "message": "Account created — awaiting admin approval."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
