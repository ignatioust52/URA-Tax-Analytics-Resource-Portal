from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import pandas as pd
from core.db_resources import resources_get_all, resources_update_approval
from backend.api.resources import clean_records
from backend.api.deps import require_admin

router = APIRouter()

class ApprovalRequest(BaseModel):
    resource_id: int
    status: str

@router.get("/pending")
def get_pending_resources(request: Request):
    require_admin(request)
    
    resources = resources_get_all()
    pending = [r for r in resources if r.get("approval_status") == "PendingApproval"]
        
    # Re-use the existing serialize formatting logic from resources.py but adapted for dicts
    return clean_records(pending)

@router.post("/approve")
async def update_approval(req: ApprovalRequest, request: Request):
    session = require_admin(request)
    user_id = session.get("user_id")
    
    if req.status not in ["Approved", "Rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    resources_update_approval(req.resource_id, req.status, user_id)
    
    # Clear cache to ensure new resources appear immediately
    from fastapi_cache import FastAPICache
    await FastAPICache.clear()
    
    return {"success": True, "message": f"Resource {req.resource_id} {req.status}"}
