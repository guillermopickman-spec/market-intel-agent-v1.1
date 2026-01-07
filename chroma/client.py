import chromadb
from chromadb.config import Settings

def get_chroma_client():
    """Returns a Chroma client with telemetry disabled to prevent PostHog errors."""
    return chromadb.Client(
        settings=Settings(
            anonymized_telemetry=False
        )
    )