import requests
import time
from services.llm.base import LLMClient
from core.settings import settings
from core.logger import get_logger
from fastapi import HTTPException

logger = get_logger("GroqClient")

class GroqClient(LLMClient):
    """
    Groq API Client - Fast inference with generous free tier.
    Free tier: ~14,400 requests/day
    """
    def __init__(self):
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "":
            logger.error("❌ GROQ_API_KEY is missing from .env")
            raise ValueError("GROQ_API_KEY is required when using Groq provider.")
        
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL_NAME
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        logger.info(f"🚀 Groq Client initialized with model: {self.model}")

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate response using Groq API.
        Uses OpenAI-compatible chat completions endpoint.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional market analyst. Output in Markdown."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048
        }

        for attempt in range(max_retries):
            try:
                logger.info(f"🚀 Groq Request: {self.model} (Attempt {attempt + 1})")
                response = requests.post(
                    url=self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=settings.LLM_REQUEST_TIMEOUT
                )

                if response.status_code == 429:
                    # Rate limit hit - wait and retry
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"⏳ Rate limit hit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                
                if content:
                    logger.info("✅ Groq Response Received.")
                    return content
                
                raise ValueError("Empty response from Groq")

            except requests.Timeout:
                logger.warning(f"⏳ Groq Request timed out after {settings.LLM_REQUEST_TIMEOUT}s (Attempt {attempt + 1})")
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=504,
                        detail=f"Groq request timed out after {settings.LLM_REQUEST_TIMEOUT}s"
                    )
                time.sleep(2)
                continue
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"⏳ Rate limit hit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"❌ Groq HTTP Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=response.status_code, detail=f"Groq Error: {str(e)}")
                time.sleep(2)
                continue
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"❌ Groq Final Failure: {str(e)}")
                    raise HTTPException(status_code=504, detail=f"Groq Error: {str(e)}")
                
                time.sleep(2)
        
        return "❌ Maximum retries reached. Groq API request failed."
