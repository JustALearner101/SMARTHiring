from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve shared root .env (`Heketon/.env`) with fallback to local `backend/.env` (e.g. inside standalone Docker)
ROOT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
LOCAL_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV_PATH), str(LOCAL_ENV_PATH)),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    PROJECT_NAME: str = "Heketon API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Security / JWT
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database (Supabase / External PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    LANGGRAPH_CHECKPOINT_DB_URI: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # LLM / AI Providers
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # LangSmith / Observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "heketon-agent"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # Experimental Feature Flags
    ENABLE_EXPERIMENTAL_ADK_AGENT: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
