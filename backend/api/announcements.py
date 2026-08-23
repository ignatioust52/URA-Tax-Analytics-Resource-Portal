from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from core.db_announcements import (
    announcements_get_active,
    announcements_get_all,
    announcements_create,
    announcements_update,
    announcements_delete
)
from backend.api.deps import require_admin, require_session, get_session_or_none

router = APIRouter()

def clean_records(records):
    if not records:
        return []
    for r in records:
        if "published_at" in r and r["published_at"]:
            r["published_at"] = str(r["published_at"])
        if "expires_at" in r and r.get("expires_at"):
            r["expires_at"] = str(r["expires_at"])
        else:
            r["expires_at"] = None
    return records

@router.get("/active")
def get_active_announcements(request: Request):
    """
    Returns active announcements for the authenticated user.
    Requires a valid session — this is an internal enterprise system.
    """
    try:
        session = require_session(request)
        # Filter by department if applicable (ABAC: department attribute)
        dept_id = session.get("department_id")
        records = announcements_get_active(dept_id)
        return clean_records(records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def get_all_announcements(request: Request):
    require_admin(request)
    try:
        records = announcements_get_all()
        return clean_records(records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    visibility: str = "EVERYONE"
    dept_id_list: list[int] = []
    expires_at: Optional[str] = None

@router.post("/")
def create_announcement(ann: AnnouncementCreate, request: Request):
    session = require_admin(request)
    try:
        announcements_create(ann.title, ann.body, ann.visibility, ann.dept_id_list, session["id"], ann.expires_at)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AnnouncementUpdate(BaseModel):
    title: str
    body: str
    visibility: str = "EVERYONE"
    dept_id_list: list[int] = []
    expires_at: Optional[str] = None
    is_active: bool

@router.put("/{announcement_id}")
def update_announcement(announcement_id: int, ann: AnnouncementUpdate, request: Request):
    require_admin(request)
    try:
        announcements_update(announcement_id, ann.title, ann.body, ann.visibility, ann.dept_id_list, ann.expires_at, ann.is_active)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: int, request: Request):
    require_admin(request)
    try:
        announcements_delete(announcement_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
