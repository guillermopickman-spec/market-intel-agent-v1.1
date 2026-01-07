import os
import sys
import asyncio
import logging
from datetime import datetime

# ==========================================================
# 1. DYNAMIC PATH CONFIGURATION (ERROR SOLUTION)
# ==========================================================
# This ensures Python finds 'database.py' and 'services/' 
# even if the script is located in a subfolder. [cite: 162]
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# Silence Configurations
os.environ["ANONYMIZED_TELEMETRY"] = "False"
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)

# ==========================================================
# 2. PROJECT IMPORTS
# ==========================================================
from database import SessionLocal
from services.agent_service import AgentService
from core.logger import get_logger

logger = get_logger("BlackwellAudit")

async def run_test_mission():
    """
    High-Stakes Mission Validation:
    Tests the agent's ability to differentiate technical contexts (GPU vs Cars)
    and the robustness of Dual orchestration (SQL + Vector). [cite: 158]
    """
    print("\n" + "🚀" * 15)
    print("MIA v1.1.0: BLACKWELL INFRASTRUCTURE AUDIT")
    print("🚀" * 15 + "\n")

    # Initialization
    db = SessionLocal()
    agent = AgentService(db=db)
    
    # Robust User Input
    user_query = (
        "Mission: Conduct a precise pricing audit for the NVIDIA B200 SXM6 GPU (Blackwell Architecture). "
        "Context: This is data center hardware, not a vehicle. Look for hourly on-demand rates from "
        "cloud providers (e.g., Lambda Labs, CoreWeave, RunPod) and compare them to the industry benchmark of $5.50/hr. "
        "Required Specs to Verify: 192GB HBM3e memory and 1000W TGP. "
        "Constraint: Do not mention cars, dealers, or automotive metrics."
    )
    
    print(f"📡 [MISSION OBJECTIVE]: {user_query[:100]}...")
    print("-" * 50)

    try:
        # Execute ReAct Loop (Planning -> Research -> Synthesis)
        mission_id = int(datetime.now().strftime("%d%H%M"))
        result = await agent.process_mission(user_query, conversation_id=mission_id)
        
        status = result.get('status', 'failed')
        report = str(result.get('report', ''))
        trace = result.get('trace', [])

        print(f"\n[MISSION STATUS]: {status.upper()}")
        print("\n🧠 [EXECUTION TRACE - AGENT REASONING]:")
        for log in trace:
            tool = log.get('tool', 'unknown')
            print(f"  - Tool: {tool.ljust(15)} | Status: {log.get('status', 'Done')}")

        print("\n📊 [FINAL REPORT (PREVIEW)]:")
        if report:
            # Print the first 600 characters of the synthesized report [cite: 161]
            print(report[:600] + "...")

        if status == "complete":
            print("\n" + "✅" * 15 + "\nMISSION SUCCESS\n" + "✅" * 15)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        logger.error(f"Mission test failed: {e}", exc_info=True)
    finally:
        db.close()
        print("\n[DB]: Connection closed.")

if __name__ == "__main__":
    asyncio.run(run_test_mission())