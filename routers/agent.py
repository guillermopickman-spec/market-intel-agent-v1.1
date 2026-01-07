from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from services.agent_service import AgentService
from core.logger import get_logger

logger = get_logger("AgentRouter")

class MissionRequest(BaseModel):
    """
    Schema for incoming mission requests.
    'user_input' matches the standard expected by the frontend/Swagger.
    """
    user_input: str
    conversation_id: Optional[int] = None

router = APIRouter(tags=["Agent"])

@router.post("/analyze")
async def analyze_mission(data: MissionRequest):
    """
    Step 1: Understand Intent
    Analyzes the user input using Gemini to identify the core mission goal 
    without triggering expensive tool executions.
    """
    try:
        agent = AgentService() 
        intent = await agent.identify_intent(data.user_input)
        return {"intent": intent}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis Error: {str(e)}"
        )

@router.post("/execute")
async def execute_mission(data: MissionRequest, db: Session = Depends(get_db)):
    """
    Step 2: Full Execution
    Triggers the ReAct loop: Planning -> Web Research -> Synthesis -> Action.
    """
    try:
        agent = AgentService(db)
        result = await agent.process_mission(data.user_input, data.conversation_id)
        return result
    except Exception as e:
        logger.error(f"Execution Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Execution Error: {str(e)}"
        )