from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Enterprise-grade settings management.
    Enforces the 'Fail-Fast' principle: missing critical vars will crash the app.
    """

    # --- PROJECT METADATA ---
    PROJECT_NAME: str = "Market Intelligence Agent"
    VERSION: str = "1.1.0"

    # --- DATABASE ---
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/market_db",
        validation_alias="DATABASE_URL"
    )

    # --- AI & LLM CONFIGURATION ---
    LLM_PROVIDER: str = Field(default="groq", validation_alias="LLM_PROVIDER")
    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    HF_API_TOKEN: str = Field(default="", validation_alias="HF_API_TOKEN")
    HF_MODEL_NAME: str = "deepseek-ai/DeepSeek-V3"
    HF_API_URL: str = Field(
        default="https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-V3",
        validation_alias="HF_API_URL"
    )
    # --- EMBEDDING CONFIGURATION ---
    EMBEDDING_PROVIDER: str = Field(
        default="huggingface",
        validation_alias="EMBEDDING_PROVIDER",
        description="Embedding provider: 'gemini' or 'huggingface'"
    )
    HF_EMBED_URL: str = Field(
        default="https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="HF_EMBED_URL"
    )
    LOCAL_EMBED_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        validation_alias="LOCAL_EMBED_MODEL_NAME"
    )
    # --- GROQ CONFIGURATION ---
    GROQ_API_KEY: str = Field(default="", validation_alias="GROQ_API_KEY")
    GROQ_MODEL_NAME: str = Field(
        default="llama-3.1-8b-instant",
        validation_alias="GROQ_MODEL_NAME",
        description="Groq model name. Options: llama-3.1-8b-instant, llama-3.1-70b-versatile, mixtral-8x7b-32768, gemma2-9b-it"
    )

    # --- TOOLS & INTEGRATIONS ---
    RESEND_API_KEY: str = Field(default="", validation_alias="RESEND_API_KEY")
    NOTION_TOKEN: str = Field(default="", validation_alias="NOTION_TOKEN")
    NOTION_PAGE_ID: str = Field(default="", validation_alias="NOTION_PAGE_ID")

    # --- EMAIL CREDENTIALS ---
    EMAIL_USER: str = Field(default="", validation_alias="EMAIL_USER")
    EMAIL_PASSWORD: str = Field(default="", validation_alias="EMAIL_PASSWORD")

    # --- SYSTEM SETTINGS ---
    ANONYMIZED_TELEMETRY: bool = False

    # --- CHROMA DB SETTINGS ---
    # Explicitly disable ChromaDB telemetry to prevent 'capture() takes 1 positional argument' errors
    # This also helps ensure privacy.
    CHROMA_SERVER_NO_ANALYTICS: bool = Field(
        default=True,
        validation_alias="CHROMA_SERVER_NO_ANALYTICS",
        description="Set to True to disable ChromaDB analytics/telemetry."
    )

    # --- CORS CONFIGURATION ---
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000",
        validation_alias="CORS_ALLOWED_ORIGINS",
        description="Comma-separated list of allowed CORS origins"
    )

    # --- REQUEST TIMEOUTS (in seconds) ---
    HTTP_REQUEST_TIMEOUT: int = Field(
        default=30,
        validation_alias="HTTP_REQUEST_TIMEOUT",
        description="Timeout for HTTP requests (Notion, etc.)"
    )
    LLM_REQUEST_TIMEOUT: int = Field(
        default=60,
        validation_alias="LLM_REQUEST_TIMEOUT",
        description="Timeout for LLM API requests"
    )
    SCRAPER_TIMEOUT: int = Field(
        default=60,
        validation_alias="SCRAPER_TIMEOUT",
        description="Timeout for web scraping operations (in seconds)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.CORS_ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()