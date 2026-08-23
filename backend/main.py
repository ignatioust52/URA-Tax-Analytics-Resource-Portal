from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables (e.g. PGHOST, PGPASSWORD) before importing API modules
load_dotenv()

from backend.api.resources import router as resources_router
from backend.api.auth import router as auth_router
from backend.api.analytics import router as analytics_router
from backend.api.governance import router as governance_router
from backend.api.users import router as users_router
from backend.api.chat import router as chat_router
from backend.api.announcements import router as announcements_router

app = FastAPI(title="URA Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ura-tax-analytics-resource-portal.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def strict_origin_csrf_middleware(request: Request, call_next):
    # Only protect state-changing requests
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        
        allowed_origins = [
            "http://localhost:3000",
            "https://ura-tax-analytics-resource-portal.onrender.com"
        ]
        
        # If Origin is present, it must strictly match
        if origin and origin not in allowed_origins:
            return JSONResponse(status_code=403, content={"detail": "CSRF verification failed: Invalid Origin"})
            
        # If no Origin, fallback to checking Referer
        if not origin and referer:
            valid_referer = any(referer.startswith(allowed) for allowed in allowed_origins)
            if not valid_referer:
                return JSONResponse(status_code=403, content={"detail": "CSRF verification failed: Invalid Referer"})
                
        # If neither is present, it's a programmatic client (like curl). 
        # In an enterprise app using session cookies, browsers ALWAYS send Origin or Referer for cross-site requests.
        # Since CORS handles preflight, and this middleware runs after, blocking requests without Origin/Referer
        # hardens against certain obscure CSRF bypasses.
        if not origin and not referer:
            return JSONResponse(status_code=403, content={"detail": "CSRF verification failed: Missing Origin/Referer"})
            
    return await call_next(request)

app.include_router(resources_router, prefix="/api/resources", tags=["Resources"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(governance_router, prefix="/api/governance", tags=["Governance"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chatbot"])
app.include_router(announcements_router, prefix="/api/announcements", tags=["Announcements"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "URA API is running"}
