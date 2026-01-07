import time
import logging
from google import genai
from core.settings import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "":
            logger.error("❌ GEMINI_API_KEY is missing from .env")
            raise ValueError("GEMINI_API_KEY is required when using Gemini provider.")

        # Using v1beta for maximum Free Tier compatibility with experimental models
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
        )

        self.candidate_models = [
            "gemini-3-flash-preview",    
            "gemini-2.5-flash-lite",
            "gemini-1.5-flash",        
            "gemini-1.5-flash-8b",     
            "gemini-2.0-flash-exp",    
        ]

        self.model_id = self._detect_usable_model()

    def _detect_usable_model(self) -> str:
        """
        Validates model availability. Includes a cooldown to prevent 429 
        errors during the startup 'Candidate Loop'.
        """
        logger.info("🔍 Initializing Gemini Free Tier System...")

        for m in self.candidate_models:
            try:
                logger.info(f"🧪 Testing connection: {m}")
                
                # CRITICAL: 5-second pause between checks. 
                # Free Tier limits 'Requests Per Minute'. Testing 4 models 
                # in 1 second is what triggers your 429 RESOURCE_EXHAUSTED.
                time.sleep(5) 
                
                resp = self.client.models.generate_content(
                    model=m,
                    contents="System check: Reply 'Ready'."
                )
                
                if resp and getattr(resp, "text", None):
                    logger.info(f"✅ Connection Established: {m}")
                    return m
            except Exception as e:
                error_snippet = str(e)[:100]
                logger.warning(f"⚠️ Model {m} skipped: {error_snippet}")

        raise RuntimeError("🛑 ALL MODELS FAILED. Your API quota is likely empty. Wait 2 minutes and try again.")

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """
        Main generation loop with exponential backoff for Free Tier rate limits.
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"🚀 [Attempt {attempt+1}] Querying {self.model_id}...")
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt
                )

                if response and getattr(response, "text", None):
                    logger.info("✅ Data retrieved successfully.")
                    return response.text #type: ignore

                return "Error: Gemini returned an empty response."

            except Exception as e:
                error_msg = str(e)

                # Robust 429/Quota detection
                if any(x in error_msg for x in ["429", "RESOURCE_EXHAUSTED", "Quota"]):
                    # Wait progressively longer: 30s, 60s, 90s
                    wait_time = (attempt + 1) * 30
                    logger.warning(f"⚠️ Quota hit! Cooling down for {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                logger.error(f"❌ Gemini SDK Error: {error_msg}")
                return f"LLM Error: {error_msg}"

        return "❌ Maximum retries reached. The Free Tier is currently saturated."