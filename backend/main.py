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
