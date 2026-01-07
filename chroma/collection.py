import chromadb
import os
import logging

logger = logging.getLogger("ChromaService")

_client_instance = None  # Declare a global variable to hold the client instance

def get_chroma_client():
    """
    Returns the singleton ChromaDB PersistentClient instance.
    Initializes it if it hasn't been already.
    """
    global _client_instance
    if _client_instance is None:
        db_path = os.path.abspath("chroma_db")
        # Removing telemetry settings from here as they seem to cause issues in 0.5.5
        _client_instance = chromadb.PersistentClient(
            path=db_path
        )
    return _client_instance

def get_collection():
    """
    Retrieves or creates the vector storage collection using the shared client.
    Includes auto-recovery for dimension mismatches.
    """
    client = get_chroma_client()  # Get the shared client
    collection_name = "document_store_v3"

    try:
        return client.get_or_create_collection(name=collection_name)
    except Exception as e:
        error_msg = str(e).lower()
        logger.warning(f"⚠️ Vector DB Check: {error_msg}")

        # Keep the dimension mismatch recovery logic, as it's separate from telemetry
        if any(keyword in error_msg for keyword in ["dimension", "index", "size"]):
            logger.error("🚨 Vector Dimension Mismatch detected. Resetting Database...")
            try:
                client.reset()
                return client.create_collection(name=collection_name)
            except Exception as reset_err:
                logger.critical(f"🛑 Critical Database Failure: {reset_err}")
                return client.get_or_create_collection(name=f"{collection_name}_emergency")

        return client.get_or_create_collection(name=collection_name)