import sys
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import os
from typing import Optional

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

# Cache ChromaDB status to avoid re-initialization on every health check
_chromadb_status: Optional[str] = None
_chromadb_initialized = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _chromadb_status, _chromadb_initialized
    
    logger.info("🚀 MIA Intelligence Systems Starting...")
    
    # Database initialization
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database Synchronization: Success")
    except Exception as e:
        logger.critical(f"❌ Database Error: {str(e)}")
    
    # Pre-initialize ChromaDB in background (non-blocking with timeout)
    # This prevents slow initialization during first health check
    async def init_chromadb():
        global _chromadb_status, _chromadb_initialized
        try:
            logger.info("🔄 Initializing ChromaDB...")
            from chroma.collection import get_chroma_client
            client = get_chroma_client()
            _ = client.list_collections()
            _chromadb_status = "up"
            _chromadb_initialized = True
            logger.info("✅ ChromaDB Initialized: Success")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB initialization warning: {str(e)}")
            _chromadb_status = f"error: {str(e)}"
            _chromadb_initialized = True  # Mark as attempted even if failed
    
    # Run ChromaDB initialization in background (non-blocking)
    # This allows the app to start quickly while ChromaDB initializes
    asyncio.create_task(init_chromadb())
    
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

@app.get("/ready", tags=["System"])
async def ready_check():
    """
    Lightweight readiness check for Render.
    Returns 200 as soon as the app is up (doesn't wait for ChromaDB).
    This allows Render to mark the service as ready quickly.
    """
    return {"status": "ready", "version": "1.1.0"}

@app.get("/health", tags=["System"])
async def health_check():
    """
    Full health check with database and ChromaDB status.
    Uses cached ChromaDB status if available to avoid re-initialization.
    """
    global _chromadb_status, _chromadb_initialized
    
    server_time = datetime.utcnow().isoformat() + "Z"

    # Database check (fast)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            db_status = "up"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # ChromaDB check (use cached status if available, otherwise check)
    if _chromadb_initialized:
        # Use cached status to avoid re-initialization
        chromadb_status = _chromadb_status or "unknown"
    else:
        # Fallback: check directly if not yet initialized
        try:
            from chroma.collection import get_chroma_client
            client = get_chroma_client()
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
