from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import pandas as pd
from core.db_resources import resources_get_all, resources_update_approval
from backend.api.resources import serialize_df
from backend.api.deps import require_admin

router = APIRouter()

class ApprovalRequest(BaseModel):
    resource_id: int
    status: str

@router.get("/pending")
def get_pending_resources(request: Request):
    require_admin(request)
    
    df = resources_get_all()
    if not df.empty and "approval_status" in df.columns:
        pending_df = df[df["approval_status"] == "PendingApproval"]
    else:
        pending_df = pd.DataFrame()
        
    return serialize_df(pending_df)

@router.post("/approve")
def update_approval(req: ApprovalRequest, request: Request):
    session = require_admin(request)
    user_id = session.get("user_id")
    
    if req.status not in ["Approved", "Rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    resources_update_approval(req.resource_id, req.status, user_id)
    return {"success": True, "message": f"Resource {req.resource_id} {req.status}"}
