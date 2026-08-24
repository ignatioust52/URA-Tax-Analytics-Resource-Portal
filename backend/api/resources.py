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
from fastapi_cache.decorator import cache

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
        
    from core.auth import has_permission
    from core.db_departments import resources_get_department_map
    from core.db_users import users_get_special_permissions
    from datetime import datetime, timezone
    
    can_view_all = has_permission(session["id"], "view_all_data")
    
    if can_view_all:
        # User has global view permission, return all approved
        return [r for r in records if r.get("approval_status") == "Approved"]

    # Filter to only Approved
    records = [r for r in records if r.get("approval_status") == "Approved"]
    if not records:
        return []
        
    active_dept_id = session.get("active_department_id")
    resource_depts = resources_get_department_map() # dict: {resource_id: [dept_name, ...]}
    
    # We need a way to map dept names to IDs or vice versa, but resource_depts returns names.
    # Let's fetch active dept name
    active_dept_name = None
    if active_dept_id:
        from core.db_departments import _fetch_one_dict
        dept_row = _fetch_one_dict("SELECT name FROM departments WHERE id = %s", (active_dept_id,))
        if dept_row:
            active_dept_name = dept_row["name"]

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
        visibility = str(row.get("visibility", "EVERYONE")).upper()
        rid = row["id"]
        
        if visibility == "ADMIN_ONLY" and not has_permission(session["id"], "manage_system_settings"):
            continue
            
        # 1. ABAC Check: Sensitivity Classification
        sensitivity = str(row.get("sensitivity_classification", "Public")).lower()
        if sensitivity in ["confidential", "restricted"]:
            required_key = f"access_{sensitivity}"
            if required_key not in active_keys:
                continue
                
        # 2. RBAC Check: Department Map
        if visibility == "SELECTED_DEPARTMENTS":
            required_depts = resource_depts.get(rid, [])
            if not active_dept_name or active_dept_name not in required_depts:
                continue

        filtered.append(row)

    return filtered

@router.get("/favorites")
@cache(expire=60)
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
@cache(expire=60)
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
@cache(expire=60)
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
    visibility: str = "EVERYONE"
    dept_id_list: List[int] = []

@router.post("/")
def create_resource(res: ResourceCreate, request: Request):
    session = require_session(request)
        
    try:
        from core.db_resources import resources_create
        new_id = resources_create(
            res.page_name, res.business_name, res.description,
            res.category, res.url, res.visibility, res.dept_id_list, session.get("email")
        )
        return {"success": True, "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{resource_id}")
async def update_resource(resource_id: int, res: ResourceCreate, request: Request):
    session = require_admin(request)
    try:
        from core.db_resources import resources_update
        resources_update(
            resource_id, res.page_name, res.business_name, res.description,
            res.category, res.url, res.visibility, res.dept_id_list, session.get("email")
        )
        from fastapi_cache import FastAPICache
        await FastAPICache.clear()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{resource_id}")
async def delete_resource(resource_id: int, business_name: str, request: Request):
    session = require_admin(request)
    try:
        from core.db_resources import resources_delete
        resources_delete(resource_id, business_name, session.get("email"))
        from fastapi_cache import FastAPICache
        await FastAPICache.clear()
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

@router.post("/{resource_id}/view")
def record_view(resource_id: int, request: Request):
    require_session(request)
    try:
        from core.db_resources import resources_record_view
        resources_record_view(resource_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
