"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration — reads from .env file or environment variables."""

    # ── LLM ──
    llm_provider: str = Field(default="ollama", description="LLM provider: ollama, groq, openai, anthropic, cohere")
    llm_model: str = Field(default="glm-5:cloud", description="Model name for the chosen provider")
    ollama_api_key: str = Field(default="", description="Ollama Cloud API key")
    llm_api_key: str = Field(default="", description="API key for non-Ollama providers")
    llm_api_base: str = Field(default="", description="Custom API base URL (optional)")
    llm_timeout: int = Field(default=120, description="LLM call timeout in seconds")
    llm_temperature: float = Field(default=0.3, description="LLM temperature (lower = more deterministic)")
    llm_max_retries: int = Field(default=3, description="Max retry attempts for failed LLM calls")

    # ── Feature Flags ──
    enable_llm_review: bool = Field(default=True, description="Enable LLM review of low-confidence rule decisions")
    review_confidence_threshold: float = Field(default=0.85, description="Rule decisions below this confidence get LLM review")

    # ── App ──
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    cors_origins: str = Field(default="*", description="Comma-separated CORS origins")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


def get_settings() -> Settings:
    """Factory function — lets FastAPI cache via Depends."""
    return Settings()
