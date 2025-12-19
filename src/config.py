"""Configuration management for the Audio Transcription Tool."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


class WhisperModel(str, Enum):
    """Available Whisper model sizes."""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Provider Keys
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    openrouter_api_key: Optional[str] = Field(default=None)

    # Default Provider
    default_llm_provider: LLMProvider = Field(default=LLMProvider.OPENROUTER)

    # OpenRouter Model
    openrouter_model: str = Field(default="anthropic/claude-sonnet-4")

    # Database
    database_url: str = Field(default="sqlite:///./data/transcriptions.db")

    # Audio Processing
    audio_storage_path: Path = Field(default=Path("./data/audio"))
    max_audio_size_mb: int = Field(default=100)
    whisper_model: WhisperModel = Field(default=WhisperModel.BASE)

    # MCP Server
    mcp_server_host: str = Field(default="localhost")
    mcp_server_port: int = Field(default=8765)

    # GitHub Integration
    github_token: Optional[str] = Field(default=None)
    github_repo: Optional[str] = Field(default=None)

    # Logging
    log_level: str = Field(default="INFO")

    def get_active_provider(self) -> LLMProvider:
        """Get the active LLM provider based on available keys."""
        if self.default_llm_provider == LLMProvider.OPENROUTER and self.openrouter_api_key:
            return LLMProvider.OPENROUTER
        elif self.default_llm_provider == LLMProvider.OPENAI and self.openai_api_key:
            return LLMProvider.OPENAI
        elif self.default_llm_provider == LLMProvider.ANTHROPIC and self.anthropic_api_key:
            return LLMProvider.ANTHROPIC
        elif self.openrouter_api_key:
            return LLMProvider.OPENROUTER
        elif self.openai_api_key:
            return LLMProvider.OPENAI
        elif self.anthropic_api_key:
            return LLMProvider.ANTHROPIC
        else:
            raise ValueError("No valid API key found for any LLM provider")

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.audio_storage_path.mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
