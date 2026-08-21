from fastapi import APIRouter, HTTPException, Request
import pandas as pd
from core.db_audit import get_audit_log
from core.db_resources import resources_get_all
from backend.api.resources import serialize_df
from backend.api.deps import require_admin

router = APIRouter()

@router.get("/")
def get_analytics(request: Request):
    require_admin(request)
    
    try:
        audit_df = get_audit_log(limit=5000)
        if audit_df.empty:
            return {"kpis": {}, "daily_views": [], "popular": [], "logs": []}
            
        audit_df["logged_at"] = pd.to_datetime(audit_df["logged_at"])
        views_df = audit_df[audit_df["action"] == "resource_view"]
        
        active_resources_df = resources_get_all()
        active_names = active_resources_df["business_name"].tolist() if not active_resources_df.empty else []
        views_df = views_df[views_df["resource_id"].isin(active_names)]
        
        if views_df.empty:
            return {"kpis": {}, "daily_views": [], "popular": [], "logs": serialize_df(audit_df)}
            
        # KPIs
        total_views = len(views_df)
        unique_users = len(views_df["user_email"].unique())
        unique_resources = len(views_df["resource_id"].unique())
        
        # Daily views trend
        views_by_date = views_df.copy()
        views_by_date["date"] = views_by_date["logged_at"].dt.date.astype(str)
        daily_views = views_by_date.groupby("date").size().reset_index(name="views")
        
        # Popular
        popular = (
            views_df.groupby("resource_id").size().reset_index(name="views")
            .sort_values("views", ascending=False).head(10)
        )
        
        return {
            "kpis": {
                "total_views": total_views,
                "unique_users": unique_users,
                "unique_resources": unique_resources
            },
            "daily_views": serialize_df(daily_views),
            "popular": serialize_df(popular),
            "logs": serialize_df(audit_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
