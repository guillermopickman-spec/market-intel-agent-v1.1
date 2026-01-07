import sys
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.settings import settings
from core.logger import get_logger
from database import engine        
from models.base import Base        
import models                       
from routers import agent, chat, documents 
from sqlalchemy import text

# Import and apply ChromaDB telemetry patch FIRST
from chroma.chroma_telemetry_patch import apply_chromadb_telemetry_patch
apply_chromadb_telemetry_patch()

# Set ChromaDB analytics environment variable as an additional measure
# (might not be necessary with the patch, but harmless)
if settings.CHROMA_SERVER_NO_ANALYTICS:
    os.environ["CHROMA_SERVER_NO_ANALYTICS"] = "1"

# ✅ KEEP ONLY THIS: Enables subprocesses for Playwright on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = get_logger("Main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 MIA Intelligence Systems Starting...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database Synchronization: Success")
    except Exception as e:
        logger.critical(f"❌ Database Error: {str(e)}")
    yield
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title="Market Intelligence Agent",
    version="1.1.0",
    lifespan=lifespan
)

cors_origins = settings.get_cors_origins()
if not cors_origins:
    logger.warning("⚠️ No CORS origins configured. API will reject all cross-origin requests.")
else:
    logger.info(f"✅ CORS enabled for origins: {', '.join(cors_origins)}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(agent.router, tags=["Agent"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(documents.router, tags=["Documents"])

@app.get("/", tags=["System"])
async def root():
    return {"status": "online", "version": "1.1.0"}

@app.get("/health", tags=["System"])
async def health_check():
    server_time = datetime.utcnow().isoformat() + "Z"

    # Database check
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            db_status = "up"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # ChromaDB vector store check
    try:
        from chroma.collection import get_chroma_client
        client = get_chroma_client()  # Now this gets the actual client
        _ = client.list_collections()
        chromadb_status = "up"
    except Exception as e:
        chromadb_status = f"error: {str(e)}"

    overall_status = (
        "ok" if db_status == "up" and chromadb_status == "up"
        else "degraded"
    )
    return {
        "server_time": server_time,
        "database": db_status,
        "chromadb": chromadb_status,
        "status": overall_status,
    }
