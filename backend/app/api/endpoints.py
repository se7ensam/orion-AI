from fastapi import APIRouter, HTTPException
from app.services.chat import ChatOrchestrator, ChatRequest, ChatResponse, get_orchestrator

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process a natural language query through the RAG pipeline.
    """
    orchestrator = get_orchestrator()
    try:
        response = await orchestrator.process_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
