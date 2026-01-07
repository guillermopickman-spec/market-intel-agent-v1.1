from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.ai_service import ask_document_question

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/ask")
async def ask_rag_question(
    query: str, 
    conversation_id: Optional[int] = Query(None, description="Context filter for a specific session")
):
    """
    RAG-powered chat endpoint.
    Retrieves relevant document chunks and synthesizes an answer.
    """
    try:
        ai_response, sources = ask_document_question(query, conversation_id=conversation_id)
        
        return {
            "query": query,
            "conversation_id": conversation_id,
            "response": ai_response,
            "sources": sources,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Chat processing error: {str(e)}"
        )