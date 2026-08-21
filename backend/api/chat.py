from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from core.ai_assistant import parse_query
from core.auth import get_active_session

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: list = []

@router.post("/")
def chat_with_ai(req: ChatRequest, request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    session = get_active_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
        
    try:
        parsed = parse_query(req.message)
        response = f"I understood your query as: {parsed['interpreted_as']}. "
        if parsed['region']:
            response += f"Pulling specific data for {parsed['region']}. "
        if parsed['tax_type']:
            response += f"Filtering for {parsed['tax_type']}. "
        if parsed['wants_underperforming']:
            response += "Highlighting underperforming metrics as requested."
            
        if not parsed['region'] and not parsed['tax_type'] and not parsed['wants_underperforming']:
            response = "I am a tax analytics assistant. Ask me about tax types (VAT, PAYE) or regions (Kampala, Gulu, etc)."
            
        return {
            "reply": response,
            "filters": {
                "region": parsed['region'],
                "tax_type": parsed['tax_type']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
