from core.settings import settings
from .huggingface import HuggingFaceClient
from .gemini import GeminiClient
from .groq import GroqClient

class LLMFactory:
    """Factory to decide which LLM provider to instantiate."""
    
    _client_instance = None  # Singleton cache to prevent re-initialization on every request
    
    @staticmethod
    def get_client():
        if LLMFactory._client_instance is None:
            provider = settings.LLM_PROVIDER.lower()
            
            if provider == "gemini":
                LLMFactory._client_instance = GeminiClient()
            elif provider == "groq":
                LLMFactory._client_instance = GroqClient()
            elif provider == "huggingface" or provider == "hf":
                LLMFactory._client_instance = HuggingFaceClient()
            else:
                # Default fallback to Hugging Face
                LLMFactory._client_instance = HuggingFaceClient()
        
        return LLMFactory._client_instance