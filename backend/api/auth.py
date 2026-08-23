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
        
    from core.db_departments import user_department_access_get_details
    departments = user_department_access_get_details(user["id"])
    
    if len(departments) == 1:
        # User has exactly one department, auto-select it
        active_department_id = departments[0]["id"]
        session_token = create_user_session(user["id"], active_department_id)
        
        response.set_cookie(
            key="session_token", 
            value=session_token, 
            httponly=True, 
            samesite="none",
            secure=True,
            max_age=3600
        )
        return {
            "success": True,
            "requires_department_selection": False,
            "user": {
                "email": user["email"],
                "role": str(user.get("role_name") or user.get("role") or "").lower(),
                "active_department_id": active_department_id
            }
        }
    else:
        # User has 0 or >1 departments, issue a temporary pre-auth token (without active_department_id)
        session_token = create_user_session(user["id"], None)
        
        response.set_cookie(
            key="session_token", 
            value=session_token, 
            httponly=True, 
            samesite="none",
            secure=True,
            max_age=3600
        )
        return {
            "success": True,
            "requires_department_selection": True,
            "departments": departments,
            "user": {
                "email": user["email"],
                "role": str(user.get("role_name") or user.get("role") or "").lower()
            }
        }

class SelectDepartmentRequest(BaseModel):
    department_id: int

@router.post("/select-department")
def select_department(req: SelectDepartmentRequest, request: Request, response: Response):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    from core.db_departments import user_department_access_get_details
    departments = user_department_access_get_details(session["user_id"])
    
    # Check if requested department is in approved list
    if not any(d["id"] == req.department_id for d in departments):
        raise HTTPException(status_code=403, detail="Not authorized for this department")
        
    # Delete old session and issue new one with department
    delete_user_session(token)
    new_token = create_user_session(session["user_id"], req.department_id)
    
    response.set_cookie(
        key="session_token", 
        value=new_token, 
        httponly=True, 
        samesite="none",
        secure=True,
        max_age=3600
    )
    return {"success": True, "active_department_id": req.department_id}

@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        delete_user_session(token)
    response.delete_cookie("session_token", samesite="none", secure=True)
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
        "active_department_id": session.get("active_department_id"),
    }

@router.get("/departments")
def get_user_departments(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    from core.db_departments import user_department_access_get_details
    deps = user_department_access_get_details(session["id"])
    return deps

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
