from fastapi import APIRouter, HTTPException
import json
import math
from core.db_resources import (
    resources_get_all,
    resources_get_favorites,
    resources_get_recent
)
from backend.api.deps import require_session, require_admin, get_session_or_none
from fastapi import Request

router = APIRouter()

def serialize_df(df):
    """Convert pandas DataFrame to a list of dicts, handling NaNs."""
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    clean_records = []
    for r in records:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                clean_r[k] = None
            else:
                clean_r[k] = v
        clean_records.append(clean_r)
    return clean_records

def filter_resources_by_rbac(df, session):
    if df.empty:
        return df
    
    # Use canonical normalized 'role' key (always lowercase)
    is_admin = session.get("role", "").lower() == "admin"
    
    if is_admin:
        # Admins can see everything (we assume main view shows all Approved and maybe PendingApproval)
        # We'll filter to just Approved for the public view, though admins can manage them in Governance
        # Wait, let's keep it simple: Admins see Approved. Governance queue handles Pending.
        if "approval_status" in df.columns:
            return df[df["approval_status"] == "Approved"]
        return df

    # Normal user filtering
    from core.db_departments import user_department_access_get, resources_get_department_map
    from core.db_users import users_get_special_permissions
    import pandas as pd
    
    # Filter to only Approved and not admin_only
    if "approval_status" in df.columns:
        df = df[df["approval_status"] == "Approved"]
    if "admin_only" in df.columns:
        df = df[df["admin_only"] == False]
        
    if df.empty:
        return df
        
    user_dept_access = set(user_department_access_get(session["id"]))
    resource_depts = resources_get_department_map() # dict: {resource_id: [dept_name, ...]}
    
    # ABAC: fetch user's special permissions
    perms = users_get_special_permissions(session["id"])
    active_keys = set()
    now_ts = pd.Timestamp.now()
    for p in perms:
        if p.get("expires_at"):
            exp = pd.to_datetime(p["expires_at"])
            if exp.tz is None:
                if exp < now_ts.tz_localize(None):
                    continue
            else:
                if exp < now_ts:
                    continue
        if p.get("permission_key"):
            active_keys.add(p["permission_key"].lower())

    def has_access(row):
        # 1. ABAC Check: Sensitivity Classification
        sensitivity = str(row.get("sensitivity_classification", "Public")).lower()
        if sensitivity in ["confidential", "restricted"]:
            required_key = f"access_{sensitivity}"
            if required_key not in active_keys:
                return False
                
        # 2. RBAC Check: Department Map
        rid = row["id"]
        required_depts = resource_depts.get(rid, [])
        if not required_depts:
            return True # No specific department restrictions, visible to all (if ABAC passed)
        return len(user_dept_access.intersection(set(required_depts))) > 0

    mask = df.apply(has_access, axis=1)
    return df[mask]

@router.get("/favorites")
def get_favorites(request: Request):
    session = require_session(request)
    fav_ids = resources_get_favorites(session["id"])
    if not fav_ids:
        return []
    df = resources_get_all()
    if df.empty:
        return []
    fav_df = df[df["id"].isin(fav_ids)].reset_index(drop=True)
    fav_df = filter_resources_by_rbac(fav_df, session)
    return serialize_df(fav_df)

@router.get("/recent")
def get_recent(request: Request):
    session = require_session(request)
    recent_records = resources_get_recent(session["id"])
    if not recent_records:
        return []
    recent_ids = list(dict.fromkeys(recent_records))
    df = resources_get_all()
    if df.empty:
        return []
    recent_df = df[df["id"].isin(recent_ids)].copy()
    if not recent_df.empty:
        recent_df['sorter'] = recent_df['id'].map({id: idx for idx, id in enumerate(recent_ids)})
        recent_df = recent_df.sort_values('sorter').drop('sorter', axis=1).reset_index(drop=True)
        recent_df = filter_resources_by_rbac(recent_df, session)
    return serialize_df(recent_df)

@router.get("/")
def get_public_resources(request: Request):
    session = require_session(request)
    try:
        df = resources_get_all()
        df = filter_resources_by_rbac(df, session)
        return serialize_df(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import List, Optional

class ResourceCreate(BaseModel):
    page_name: str
    business_name: str
    description: str = ""
    category: str = ""
    url: str
    admin_only: bool = False
    dept_id_list: List[int] = []

@router.post("/")
def create_resource(res: ResourceCreate, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    try:
        from core.db_resources import resources_create
        new_id = resources_create(
            res.page_name, res.business_name, res.description,
            res.category, res.url, res.admin_only, res.dept_id_list, session.get("email")
        )
        return {"success": True, "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{resource_id}")
def update_resource(resource_id: int, res: ResourceCreate, request: Request):
    session = require_admin(request)
    try:
        from core.db_resources import resources_update
        resources_update(
            resource_id, res.page_name, res.business_name, res.description,
            res.category, res.url, res.admin_only, res.dept_id_list, session.get("email")
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{resource_id}")
def delete_resource(resource_id: int, business_name: str, request: Request):
    session = require_admin(request)
    try:
        from core.db_resources import resources_delete
        resources_delete(resource_id, business_name, session.get("email"))
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/favorites/{resource_id}")
def toggle_favorite(resource_id: int, request: Request):
    session = require_session(request)
    try:
        from core.db_resources import resources_toggle_favorite
        is_fav = resources_toggle_favorite(session["id"], resource_id)
        return {"success": True, "is_favorite": is_fav}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
