from fastapi import APIRouter, HTTPException, Request
import pandas as pd
import math
from core.db_audit import get_audit_log
from core.db_resources import resources_get_all
from backend.api.resources import clean_records
from backend.api.deps import require_admin
from fastapi_cache.decorator import cache

router = APIRouter()

def serialize_df(df):
    """Convert pandas DataFrame to a list of dicts, handling NaNs."""
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    clean = []
    for r in records:
        clean_r = {}
        for k, v in r.items():
            if isinstance(v, float) and math.isnan(v):
                clean_r[k] = None
            else:
                clean_r[k] = v
        clean.append(clean_r)
    return clean

@router.get("/")
@cache(expire=60)
def get_analytics(request: Request):
    require_admin(request)
    
    try:
        audit_logs = get_audit_log(limit=5000)
        if not audit_logs:
            return {"kpis": {}, "daily_views": [], "popular": [], "logs": []}
            
        audit_df = pd.DataFrame(audit_logs)
        audit_df["logged_at"] = pd.to_datetime(audit_df["logged_at"])
        views_df = audit_df[audit_df["action"] == "resource_view"]
        
        active_resources = resources_get_all()
        active_names = [r["business_name"] for r in active_resources] if active_resources else []
        views_df = views_df[views_df["resource_id"].isin(active_names)]
        
        if views_df.empty:
            return {"kpis": {}, "daily_views": [], "popular": [], "logs": clean_records(audit_logs)}
            
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
            "logs": clean_records(audit_logs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
