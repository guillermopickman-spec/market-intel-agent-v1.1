import logging
import requests
import time
from typing import List, Optional, Union
from google import genai
from core.settings import settings

logger = logging.getLogger(__name__)

class GeminiEmbedder:
    """
    Handles high-performance 768-dimension vector generation 
    using Google Gemini text-embedding-004.
    """
    def __init__(self):
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "":
            logger.error("❌ GEMINI_API_KEY is missing for embeddings")
            raise ValueError("GEMINI_API_KEY is required when using Gemini embeddings.")

        # Client initialization (Ready for Docker/Render)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "text-embedding-004"

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Converts a list of strings into high-dimensional numerical vectors.
        """
        if not texts:
            return []

        try:
            logger.info(f"📡 Requesting 768-dim Vectors for {len(texts)} chunks...")
            
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=texts
            )
            
            if not result or not hasattr(result, "embeddings") or not result.embeddings:
                logger.error("❌ Gemini returned an empty or invalid embedding result")
                return []

            # Precise extraction logic for strict typing
            embeddings: List[List[float]] = [
                list(e.values) for e in result.embeddings 
                if e is not None and e.values is not None
            ]
            
            logger.info(f"✅ Received {len(embeddings)} vectors.")
            return embeddings
                
        except Exception as e:
            logger.error(f"❌ Gemini Embedding Error: {e}")
            return []


class HuggingFaceEmbedder:
    """
    Handles 384-dimension vector generation using HuggingFace Inference API.
    Uses sentence-transformers/all-MiniLM-L6-v2 (free, no quota issues).
    """
    def __init__(self):
        self.api_url = settings.HF_EMBED_URL
        self.token = settings.HF_API_TOKEN
        # Note: HF embeddings can work without token for public models, but token is recommended
        if self.token:
            logger.info(f"🚀 HuggingFace Embedder initialized: {self.api_url}")
        else:
            logger.warning(f"⚠️ HuggingFace Embedder initialized without token (public models only): {self.api_url}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Converts a list of strings into 384-dimension vectors via HF Inference API.
        """
        if not texts:
            return []

        try:
            logger.info(f"📡 Requesting 384-dim Vectors for {len(texts)} chunks via HuggingFace...")
            
            headers = {
                "Authorization": f"Bearer {self.token}" if self.token else None,
                "Content-Type": "application/json"
            }
            # Remove None values from headers
            headers = {k: v for k, v in headers.items() if v is not None}
            
            payload = {
                "inputs": texts
            }

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    response = requests.post(
                        url=self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 503:
                        # Model is warming up
                        wait_time = 15 * (attempt + 1)
                        logger.warning(f"⏳ HF Embedding model warming up... waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    embeddings = response.json()

                    # HF returns a list of lists (one vector per text)
                    if isinstance(embeddings, list) and len(embeddings) > 0:
                        # Ensure all are lists of floats
                        result: List[List[float]] = [
                            list(emb) if isinstance(emb, list) else emb 
                            for emb in embeddings
                        ]
                        logger.info(f"✅ Received {len(result)} vectors from HuggingFace.")
                        return result
                    else:
                        logger.error("❌ HuggingFace returned invalid embedding format")
                        return []

                except requests.exceptions.HTTPError as e:
                    if response.status_code == 503:
                        wait_time = 15 * (attempt + 1)
                        logger.warning(f"⏳ HF Embedding model warming up... waiting {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    logger.error(f"❌ HuggingFace Embedding HTTP Error: {e}")
                    if attempt == max_attempts - 1:
                        return []
                    time.sleep(5)
                    continue
                except Exception as e:
                    logger.error(f"❌ HuggingFace Embedding Error: {e}")
                    if attempt == max_attempts - 1:
                        return []
                    time.sleep(2)

            return []

        except Exception as e:
            logger.error(f"❌ HuggingFace Embedding Error: {e}")
            return []


class LocalSentenceTransformerEmbedder:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model_name = settings.LOCAL_EMBED_MODEL_NAME
        self.model = SentenceTransformer(self.model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()


# Singleton Instance Management
_model: Optional[Union[GeminiEmbedder, HuggingFaceEmbedder, LocalSentenceTransformerEmbedder]] = None

def get_embedding_model():
    global _model
    if _model is None:
        provider = settings.EMBEDDING_PROVIDER.lower()
        if provider == "gemini":
            _model = GeminiEmbedder()
        elif provider in ("local", "sentence_transformers", "sentence-transformers"):
            _model = LocalSentenceTransformerEmbedder()
        else:
            _model = HuggingFaceEmbedder()
    return _model