import json
import re
import asyncio
import concurrent.futures
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from core.logger import get_logger
from core.settings import settings
from core.prompts import CLOUD_AGENT_PROMPT, REPORT_SYNTHESIS_PROMPT
from core.validators import validate_url
from services.llm.factory import LLMFactory

from services.scraper_service import scrape_web 
from services.notion_service import NotionService
from services.email_service import EmailService
from services.search_service import SearchService
from services.document_service import ingest_document 
import models 

logger = get_logger("AgentService")

class AgentService:
    def __init__(self, db: Optional[Session] = None):
        try:
            self.llm = LLMFactory.get_client()
            self.db = db
            self.notion = NotionService()
            self.email = EmailService()
            self.search_tool = SearchService()
            self.current_intel = "" 
            logger.info("🤖 MIA Agent Service v0.2.1 initialized (Gemini Optimized).")
        except Exception as e:
            logger.critical(f"🛑 Failed to initialize AgentService: {str(e)}")
            raise

    async def identify_intent(self, user_input: str) -> str:
        """
        REQUIRED BY ROUTER: Quickly identifies the goal of the user query.
        This prevents the 500 error on the /analyze endpoint.
        """
        logger.info(f"🧠 Identifying intent for: {user_input[:30]}...")
        prompt = f"Identify the core intent of this market intelligence query in 3 words: {user_input}"
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self.llm.generate, prompt)
        except Exception as e:
            logger.error(f"Intent Identification Error: {e}")
            return "General Intelligence Gathering"

    async def generate_plan(self, user_input: str) -> List[Dict[str, Any]]:
        """Creates a structured execution plan using Gemini."""
        logger.info(f"📋 Generating execution plan for: '{user_input[:50]}...'")
        prompt = CLOUD_AGENT_PROMPT.format(user_input=user_input)
        
        loop = asyncio.get_running_loop()
        raw_response = await loop.run_in_executor(None, self.llm.generate, prompt)
        match = re.search(r"(\[.*\])", raw_response, re.DOTALL)
        
        if not match:
            logger.error("❌ Gemini failed to return a valid JSON plan array.")
            return []

        try:
            plan = json.loads(match.group(1))
            logger.info(f"✅ Plan generated with {len(plan)} steps.")
            return plan
        except json.JSONDecodeError:
            logger.error("❌ Critical JSON Parse Error in Agent Plan.")
            return []

    def _integrity_check(self, content: str) -> str:
        """Professional safeguard against hallucinated or empty data."""
        forbidden = ["placeholder", "insert here", "no data found", "error"]
        if not content or len(str(content)) < 50 or any(p in str(content).lower() for p in forbidden):
            logger.warning("⚠️ Data integrity check failed.")
            return self.current_intel if self.current_intel else "Mission failed: No meaningful data gathered."
        return content

    def _persist_to_memory(self, report: str, conversation_id: int):
        """Dual-Layer Persistence: Vector (RAG) & SQL (Audit)."""
        logger.info(f"💾 Persisting report to dual-layer memory.")
        try:
            ingest_document(
                title=f"Report_{conversation_id}_{datetime.now().strftime('%Y%m%d')}", 
                content=report, 
                conversation_id=conversation_id
            )
            
            if self.db:
                new_log = models.MissionLog(
                    conversation_id=conversation_id,
                    query="Market Intelligence Mission",
                    response=report,
                    status="COMPLETED"
                )
                self.db.add(new_log)
                self.db.commit()
                logger.info("✅ Persistence successful.")
        except Exception as e:
            logger.error(f"❌ Memory Persistence Error: {str(e)}")

    async def execute_tool(self, tool: str, args: Dict[str, Any], conversation_id: int = 0) -> str:
        """Universal Tool Orchestrator - Updated for Async compatibility."""
        logger.info(f"🛠️ Executing Tool: {tool}")
        try:
            if tool == "web_research":
                url = args.get("url") or args.get("link")
                if not url:
                    return "Error: No URL provided for web_research"
                
                url_str = str(url).strip()
                is_valid, error_msg = validate_url(url_str)
                if not is_valid:
                    logger.warning(f"Invalid URL rejected: {url_str} - {error_msg}")
                    return f"Error: Invalid URL - {error_msg}"
                
                result = await scrape_web(url_str, conversation_id)
                
                if any(m in result.lower() for m in ["cookie", "blocked", "verify", "robot"]) or len(result) < 500:
                    logger.warning(f"🛡️ Protection detected on {url}. Falling back.")
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(None, self.search_tool.search, f"Latest info from {url}")
                return result

            loop = asyncio.get_running_loop()
            
            if tool == "web_search":
                query = args.get("query") or "Market Intelligence Query"
                return await loop.run_in_executor(None, self.search_tool.search, str(query))
            
            if tool == "save_to_notion":
                title = args.get("title", f"Report {datetime.now().date()}")
                content = self._integrity_check(args.get("content", ""))
                return "✅ Notion OK" if await loop.run_in_executor(None, self.notion.create_page, title, content) else "❌ Notion Error"
            
            if tool == "dispatch_email":
                content = self._integrity_check(args.get("content", ""))
                success = await loop.run_in_executor(None, self.email.send_email, settings.EMAIL_USER, f"Agent Report: {args.get('title', 'Update')}", content)
                return "✅ Email OK" if success else "❌ Email Error"
            
            return f"Error: Tool '{tool}' not found."
        except Exception as e:
            logger.error(f"❌ Tool Execution Failure ({tool}): {str(e)}")
            return f"Tool Failure: {str(e)}"

    async def process_mission(self, user_input: str, conversation_id: Optional[int] = None) -> Dict[str, Any]:
        """Simplified Orchestration Loop using the updated execute_tool."""
        mission_id = conversation_id or 999
        logger.info(f"🏁 Mission {mission_id} started.")
        
        plan = await self.generate_plan(user_input)
        self.current_intel = ""
        logs = []
        
        for step in [s for s in plan if s.get('tool') in ["web_research", "web_search"]]:
            res = await self.execute_tool(step['tool'], step['args'], mission_id)
            self.current_intel += f"\n---\n{res}\n"
            logs.append({"tool": step['tool'], "status": "Gathered"})

        loop = asyncio.get_running_loop()
        self.current_intel = await loop.run_in_executor(
            None, 
            self.llm.generate, 
            REPORT_SYNTHESIS_PROMPT.format(intel_pool=self.current_intel)
        )
        self._persist_to_memory(self.current_intel, mission_id)

        for step in [s for s in plan if s.get('tool') in ["save_to_notion", "dispatch_email"]]:
            step['args']['content'] = self.current_intel
            res = await self.execute_tool(step['tool'], step['args'], mission_id)
            logs.append({"tool": step['tool'], "result": res})

        logger.info(f"🏆 Mission {mission_id} complete.")
        return {
            "status": "complete", 
            "mission_id": mission_id,
            "report": self.current_intel, 
            "trace": logs
        }