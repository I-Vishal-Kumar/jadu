"""LLM Provider Factory for multi-provider support."""

from typing import Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from src.config import settings, LLMProvider


class LLMProviderFactory:
    """Factory for creating LLM instances from different providers."""

    @staticmethod
    def create_openai(
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ChatOpenAI:
        """Create an OpenAI chat model."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openai_api_key,
            **kwargs,
        )

    @staticmethod
    def create_anthropic(
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.0,
        max_tokens: Optional[int] = 4096,
        **kwargs,
    ) -> ChatAnthropic:
        """Create an Anthropic chat model."""
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.anthropic_api_key,
            **kwargs,
        )

    @staticmethod
    def create_openrouter(
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = 4096,
        **kwargs,
    ) -> ChatOpenAI:
        """Create an OpenRouter chat model (uses OpenAI-compatible API)."""
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")

        # Use configured model or default
        model = model or settings.openrouter_model

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Audio Transcription Tool",
            },
            **kwargs,
        )

    @classmethod
    def create(
        cls,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> BaseChatModel:
        """Create an LLM instance based on provider."""
        if provider is None:
            provider = settings.get_active_provider()

        if provider == LLMProvider.OPENROUTER:
            return cls.create_openrouter(
                model=model,
                temperature=temperature,
                **kwargs,
            )
        elif provider == LLMProvider.OPENAI:
            return cls.create_openai(
                model=model or "gpt-4o",
                temperature=temperature,
                **kwargs,
            )
        elif provider == LLMProvider.ANTHROPIC:
            return cls.create_anthropic(
                model=model or "claude-sonnet-4-20250514",
                temperature=temperature,
                **kwargs,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    **kwargs,
) -> BaseChatModel:
    """Convenience function to get an LLM instance."""
    llm_provider = LLMProvider(provider) if provider else None
    return LLMProviderFactory.create(
        provider=llm_provider,
        model=model,
        temperature=temperature,
        **kwargs,
    )


def get_chat_model(
    task: str = "general",
    provider: Optional[str] = None,
) -> BaseChatModel:
    """Get a chat model optimized for a specific task."""
    # Task-specific configurations
    task_configs = {
        "transcription": {"temperature": 0.0},
        "translation": {"temperature": 0.3},
        "summarization": {"temperature": 0.5},
        "intent_detection": {"temperature": 0.0},
        "keyword_extraction": {"temperature": 0.0},
        "general": {"temperature": 0.7},
    }

    config = task_configs.get(task, task_configs["general"])
    llm_provider = LLMProvider(provider) if provider else None

    return LLMProviderFactory.create(
        provider=llm_provider,
        **config,
    )
