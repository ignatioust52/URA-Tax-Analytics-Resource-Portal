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

def clean_records(records):
    """Convert list of dicts to handle NaNs and date formatting (formerly serialize_df)."""
    if not records:
        return []
    clean = []
    for r in records:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                clean_r[k] = None
            else:
                clean_r[k] = v
            # Date formatting handled by Fastapi/Pydantic mostly, but stringify timestamps if needed
            if k in ("created_at", "updated_at", "last_viewed_at") and v:
                clean_r[k] = str(v)
        clean.append(clean_r)
    return clean

def filter_resources_by_rbac(records, session):
    if not records:
        return []
    
    # Use canonical normalized 'role' key (always lowercase)
    is_admin = session.get("role", "").lower() == "admin"
    
    if is_admin:
        # Admins can see everything (we assume main view shows all Approved and maybe PendingApproval)
        # We'll filter to just Approved for the public view, though admins can manage them in Governance
        return [r for r in records if r.get("approval_status") == "Approved"]

    # Normal user filtering
    from core.db_departments import user_department_access_get, resources_get_department_map
    from core.db_users import users_get_special_permissions
    from datetime import datetime, timezone
    
    # Filter to only Approved and not admin_only
    records = [r for r in records if r.get("approval_status") == "Approved" and not r.get("admin_only")]
        
    if not records:
        return []
        
    user_dept_access = set(user_department_access_get(session["id"]))
    resource_depts = resources_get_department_map() # dict: {resource_id: [dept_name, ...]}
    
    # ABAC: fetch user's special permissions
    perms = users_get_special_permissions(session["id"])
    active_keys = set()
    now_ts = datetime.now(timezone.utc)
    for p in perms:
        if p.get("expires_at"):
            exp = p["expires_at"]
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now_ts:
                continue
        if p.get("permission_key"):
            active_keys.add(p["permission_key"].lower())

    filtered = []
    for row in records:
        # 1. ABAC Check: Sensitivity Classification
        sensitivity = str(row.get("sensitivity_classification", "Public")).lower()
        if sensitivity in ["confidential", "restricted"]:
            required_key = f"access_{sensitivity}"
            if required_key not in active_keys:
                continue
                
        # 2. RBAC Check: Department Map
        rid = row["id"]
        required_depts = resource_depts.get(rid, [])
        if not required_depts:
            filtered.append(row) # No specific department restrictions, visible to all (if ABAC passed)
        elif len(user_dept_access.intersection(set(required_depts))) > 0:
            filtered.append(row)

    return filtered

@router.get("/favorites")
def get_favorites(request: Request):
    session = require_session(request)
    fav_ids = set(resources_get_favorites(session["id"]))
    if not fav_ids:
        return []
    records = resources_get_all()
    if not records:
        return []
    fav_records = [r for r in records if r["id"] in fav_ids]
    fav_records = filter_resources_by_rbac(fav_records, session)
    return clean_records(fav_records)

@router.get("/recent")
def get_recent(request: Request):
    session = require_session(request)
    recent_records_ids = resources_get_recent(session["id"])
    if not recent_records_ids:
        return []
    recent_ids = list(dict.fromkeys(recent_records_ids))
    records = resources_get_all()
    if not records:
        return []
    
    recent_records = [r for r in records if r["id"] in recent_ids]
    # Sort by recent_ids order
    id_to_idx = {id: idx for idx, id in enumerate(recent_ids)}
    recent_records.sort(key=lambda x: id_to_idx.get(x["id"], 9999))
    
    if recent_records:
        recent_records = filter_resources_by_rbac(recent_records, session)
    return clean_records(recent_records)

@router.get("/")
def get_public_resources(request: Request):
    session = require_session(request)
    try:
        records = resources_get_all()
        records = filter_resources_by_rbac(records, session)
        return clean_records(records)
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
