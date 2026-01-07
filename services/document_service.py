import uuid
import datetime
from typing import Optional, List, cast
from chromadb.api.types import Metadatas # Import the specific type
from core.logger import get_logger
from chroma.collection import get_collection
from embeddings.chunker import chunk_text
from embeddings.model import get_embedding_model

logger = get_logger("DocumentService")

def ingest_document(title: str, content: str, conversation_id: Optional[int] = None) -> int:
    """
    Hardened Ingestion: Pylance-safe and optimized for ChromaDB 2026.
    """
    try:
        collection = get_collection()

        # 1. Chunking
        chunks = chunk_text(content)
        if not chunks:
            logger.warning(f"No content for: {title}")
            return 0
            
        # 2. Preparation
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        # 3. Metadata (Explicitly Cast for Pylance)
        # Chroma expects a List of Dictionaries where values are specific primitives
        raw_metadatas = [
            {
                "title": str(title),
                "conversation_id": int(conversation_id or 0),
                "timestamp": datetime.datetime.now().isoformat()
            } for _ in chunks
        ]
        
        # Use cast to satisfy the Type Checker's invariance rules
        safe_metadatas = cast(Metadatas, raw_metadatas)

        # 4. Generate embeddings
        model = get_embedding_model()
        embeddings = model.embed(chunks)
        if not embeddings:
            logger.error("No embeddings generated during ingest")
            return 0

        # 5. Storage 
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=safe_metadatas,
            embeddings=embeddings,
        )
        
        logger.info(f"✅ Ingested {len(chunks)} chunks for mission {conversation_id}.")
        return len(chunks)
        
    except Exception as e:
        logger.error(f"Ingestion Error: {str(e)}")
        return 0