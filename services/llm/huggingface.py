import requests
import time
from services.llm.base import LLMClient
from core.settings import settings
from core.logger import get_logger
from fastapi import HTTPException

logger = get_logger("HuggingFaceClient")

class HuggingFaceClient(LLMClient):
    def __init__(self):
        if not settings.HF_API_TOKEN or settings.HF_API_TOKEN == "":
            logger.error("❌ HF_API_TOKEN is missing from .env")
            raise ValueError("HF_API_TOKEN is required when using HuggingFace provider.")
        
        self.api_url = settings.HF_API_URL
        self.token = settings.HF_API_TOKEN
        self.model = settings.HF_MODEL_NAME 

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional market analyst. Output in Markdown."},
                {"role": "user", "content": prompt}
            ],
            "parameters": {"max_new_tokens": 1024, "temperature": 0.1}
        }

        max_attempts = 6 
        for attempt in range(max_attempts):
            try:
                logger.info(f"🚀 HF Request: {self.model} (Attempt {attempt + 1})")
                response = requests.post(
                    url=self.api_url, 
                    headers=headers,
                    json=payload,
                    timeout=settings.LLM_REQUEST_TIMEOUT
                )
                
                if response.status_code == 503:
                    logger.warning(f"⏳ HF Model is warming up... waiting 15s.")
                    time.sleep(15)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, list): data = data[0]
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                
                if content:
                    logger.info("✅ LLM Response Received.")
                    return content
                
                raise ValueError("Empty response from Hugging Face")

            except requests.Timeout:
                logger.warning(f"⏳ HF Request timed out after {settings.LLM_REQUEST_TIMEOUT}s (Attempt {attempt + 1})")
                if attempt == max_attempts - 1:
                    raise HTTPException(
                        status_code=504, 
                        detail=f"AI request timed out after {settings.LLM_REQUEST_TIMEOUT}s"
                    )
                time.sleep(5)
                continue
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"❌ HF Final Failure: {str(e)}")
                    raise HTTPException(status_code=504, detail=f"AI Error: {str(e)}")
                
                time.sleep(5)
        
        return "IA Connection Error."