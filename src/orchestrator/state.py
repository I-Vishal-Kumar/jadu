"""State definitions for the orchestrator workflow."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class ProcessingTask(str, Enum):
    """Available processing tasks."""

    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"
    SUMMARIZE = "summarize"
    DETECT_INTENT = "detect_intent"
    EXTRACT_KEYWORDS = "extract_keywords"
    FULL_PIPELINE = "full_pipeline"


class TaskStatus(str, Enum):
    """Status of a processing task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Result from a single task execution."""

    task: ProcessingTask
    status: TaskStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class WorkflowState(TypedDict, total=False):
    """State object passed through the workflow graph."""

    # Input
    audio_file_path: str
    audio_file_id: Optional[int]
    tasks: List[ProcessingTask]

    # Processing options
    source_language: str
    target_languages: List[str]
    include_timestamps: bool
    summary_type: str
    max_keywords: int

    # Intermediate results
    transcript_text: Optional[str]
    transcript_id: Optional[int]
    detected_language: Optional[str]

    # Task results
    transcription_result: Optional[Dict[str, Any]]
    translation_results: Optional[List[Dict[str, Any]]]
    summary_result: Optional[Dict[str, Any]]
    intent_result: Optional[Dict[str, Any]]
    keyword_result: Optional[Dict[str, Any]]

    # Workflow control
    current_task: Optional[ProcessingTask]
    task_history: List[TaskResult]
    errors: List[str]

    # Metadata
    started_at: Optional[str]
    completed_at: Optional[str]
    total_duration_seconds: Optional[float]


def create_initial_state(
    audio_file_path: str,
    tasks: List[ProcessingTask],
    audio_file_id: Optional[int] = None,
    source_language: str = "en",
    target_languages: Optional[List[str]] = None,
    include_timestamps: bool = False,
    summary_type: str = "general",
    max_keywords: int = 20,
) -> WorkflowState:
    """Create an initial workflow state."""
    return WorkflowState(
        audio_file_path=audio_file_path,
        audio_file_id=audio_file_id,
        tasks=tasks,
        source_language=source_language,
        target_languages=target_languages or [],
        include_timestamps=include_timestamps,
        summary_type=summary_type,
        max_keywords=max_keywords,
        transcript_text=None,
        transcript_id=None,
        detected_language=None,
        transcription_result=None,
        translation_results=None,
        summary_result=None,
        intent_result=None,
        keyword_result=None,
        current_task=None,
        task_history=[],
        errors=[],
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
        total_duration_seconds=None,
    )
