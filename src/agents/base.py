"""Base agent class for all specialized agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

from src.llm.provider import get_chat_model
from src.mcp.tools import DatabaseTools


class AgentResult(BaseModel):
    """Result from an agent execution."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """Base class for all agents in the system."""

    def __init__(
        self,
        name: str,
        description: str,
        llm: Optional[BaseChatModel] = None,
        provider: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.llm = llm or get_chat_model(task=self._get_task_type(), provider=provider)
        self.db_tools = DatabaseTools()
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def _get_task_type(self) -> str:
        """Return the task type for LLM configuration."""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        """Execute the agent's main task."""
        pass

    def _log_start(self, operation: str, **kwargs) -> None:
        """Log the start of an operation."""
        self.logger.info(f"Starting {operation} with params: {kwargs}")

    def _log_complete(self, operation: str, result: AgentResult) -> None:
        """Log the completion of an operation."""
        if result.success:
            self.logger.info(f"Completed {operation} successfully")
        else:
            self.logger.error(f"Failed {operation}: {result.error}")

    def _create_error_result(self, error: str) -> AgentResult:
        """Create an error result."""
        return AgentResult(success=False, error=error)

    def _create_success_result(
        self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Create a success result."""
        return AgentResult(success=True, data=data, metadata=metadata)
