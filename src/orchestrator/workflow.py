"""Orchestrator workflow using LangGraph for coordinating agents."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from src.agents import (
    TranscriptionAgent,
    TranslationAgent,
    SummarizationAgent,
    IntentDetectionAgent,
    KeywordExtractionAgent,
)
from src.orchestrator.state import (
    ProcessingTask,
    TaskResult,
    TaskStatus,
    WorkflowState,
    create_initial_state,
)

logger = logging.getLogger(__name__)


class AudioTranscriptionOrchestrator:
    """
    Orchestrator that coordinates multiple agents to process audio files.

    Uses LangGraph to build a workflow graph that can:
    1. Transcribe audio files
    2. Translate transcripts
    3. Summarize content
    4. Detect intents
    5. Extract keywords

    The workflow is dynamic based on the requested tasks.
    """

    def __init__(self, provider: Optional[str] = None):
        """Initialize the orchestrator with agents."""
        self.provider = provider

        # Initialize agents
        self.transcription_agent = TranscriptionAgent(provider=provider)
        self.translation_agent = TranslationAgent(provider=provider)
        self.summarization_agent = SummarizationAgent(provider=provider)
        self.intent_agent = IntentDetectionAgent(provider=provider)
        self.keyword_agent = KeywordExtractionAgent(provider=provider)

        # Build the workflow graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(WorkflowState)

        # Add nodes for each task
        workflow.add_node("router", self._route_task)
        workflow.add_node("transcribe", self._transcribe_node)
        workflow.add_node("translate", self._translate_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("detect_intent", self._detect_intent_node)
        workflow.add_node("extract_keywords", self._extract_keywords_node)
        workflow.add_node("finalize", self._finalize_node)

        # Set entry point
        workflow.set_entry_point("router")

        # Add conditional edges from router
        workflow.add_conditional_edges(
            "router",
            self._get_next_task,
            {
                "transcribe": "transcribe",
                "translate": "translate",
                "summarize": "summarize",
                "detect_intent": "detect_intent",
                "extract_keywords": "extract_keywords",
                "finalize": "finalize",
            },
        )

        # All task nodes route back to router
        for node in ["transcribe", "translate", "summarize", "detect_intent", "extract_keywords"]:
            workflow.add_edge(node, "router")

        # Finalize leads to end
        workflow.add_edge("finalize", END)

        return workflow.compile()

    def _get_next_task(
        self, state: WorkflowState
    ) -> Literal["transcribe", "translate", "summarize", "detect_intent", "extract_keywords", "finalize"]:
        """Determine the next task to execute."""
        tasks = state.get("tasks", [])
        completed_tasks = {
            result.task for result in state.get("task_history", [])
            if result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]
        }

        # Handle full pipeline - expand to all tasks
        if ProcessingTask.FULL_PIPELINE in tasks:
            tasks = [
                ProcessingTask.TRANSCRIBE,
                ProcessingTask.TRANSLATE,
                ProcessingTask.SUMMARIZE,
                ProcessingTask.DETECT_INTENT,
                ProcessingTask.EXTRACT_KEYWORDS,
            ]

        # Find next uncompleted task
        for task in tasks:
            if task not in completed_tasks:
                # Check dependencies
                if task != ProcessingTask.TRANSCRIBE and not state.get("transcript_text"):
                    # Need transcription first
                    if ProcessingTask.TRANSCRIBE not in completed_tasks:
                        return "transcribe"
                    else:
                        # Transcription completed but no text - skip dependent tasks
                        continue

                return task.value

        return "finalize"

    def _route_task(self, state: WorkflowState) -> WorkflowState:
        """Router node - just passes state through."""
        return state

    async def _transcribe_node(self, state: WorkflowState) -> WorkflowState:
        """Execute transcription."""
        logger.info("Executing transcription task")
        started_at = datetime.utcnow()

        try:
            result = await self.transcription_agent.execute(
                audio_file_path=state["audio_file_path"],
                audio_file_id=state.get("audio_file_id"),
                language=state.get("source_language"),
                include_timestamps=state.get("include_timestamps", False),
            )

            if result.success:
                state["transcript_text"] = result.data["text"]
                state["transcript_id"] = result.data.get("transcript_id")
                state["detected_language"] = result.data.get("language", "en")
                state["transcription_result"] = result.data

                state["task_history"].append(TaskResult(
                    task=ProcessingTask.TRANSCRIBE,
                    status=TaskStatus.COMPLETED,
                    data=result.data,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))
            else:
                state["errors"].append(f"Transcription failed: {result.error}")
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.TRANSCRIBE,
                    status=TaskStatus.FAILED,
                    error=result.error,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))

        except Exception as e:
            logger.exception("Transcription node failed")
            state["errors"].append(f"Transcription error: {str(e)}")
            state["task_history"].append(TaskResult(
                task=ProcessingTask.TRANSCRIBE,
                status=TaskStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))

        return state

    async def _translate_node(self, state: WorkflowState) -> WorkflowState:
        """Execute translation."""
        logger.info("Executing translation task")
        started_at = datetime.utcnow()

        target_languages = state.get("target_languages", [])
        if not target_languages:
            state["task_history"].append(TaskResult(
                task=ProcessingTask.TRANSLATE,
                status=TaskStatus.SKIPPED,
                data={"reason": "No target languages specified"},
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))
            return state

        transcript_text = state.get("transcript_text")
        if not transcript_text:
            state["task_history"].append(TaskResult(
                task=ProcessingTask.TRANSLATE,
                status=TaskStatus.SKIPPED,
                data={"reason": "No transcript available"},
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))
            return state

        try:
            results = await self.translation_agent.translate_to_multiple(
                text=transcript_text,
                target_languages=target_languages,
                source_language=state.get("detected_language", "en"),
                transcript_id=state.get("transcript_id"),
            )

            translation_data = []
            for result in results:
                if result.success:
                    translation_data.append(result.data)
                else:
                    state["errors"].append(f"Translation failed: {result.error}")

            state["translation_results"] = translation_data
            state["task_history"].append(TaskResult(
                task=ProcessingTask.TRANSLATE,
                status=TaskStatus.COMPLETED if translation_data else TaskStatus.FAILED,
                data={"translations": translation_data},
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))

        except Exception as e:
            logger.exception("Translation node failed")
            state["errors"].append(f"Translation error: {str(e)}")
            state["task_history"].append(TaskResult(
                task=ProcessingTask.TRANSLATE,
                status=TaskStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))

        return state

    async def _summarize_node(self, state: WorkflowState) -> WorkflowState:
        """Execute summarization."""
        logger.info("Executing summarization task")
        started_at = datetime.utcnow()

        transcript_text = state.get("transcript_text")
        if not transcript_text:
            state["task_history"].append(TaskResult(
                task=ProcessingTask.SUMMARIZE,
                status=TaskStatus.SKIPPED,
                data={"reason": "No transcript available"},
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))
            return state

        try:
            result = await self.summarization_agent.execute(
                text=transcript_text,
                summary_type=state.get("summary_type", "general"),
                transcript_id=state.get("transcript_id"),
            )

            if result.success:
                state["summary_result"] = result.data
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.SUMMARIZE,
                    status=TaskStatus.COMPLETED,
                    data=result.data,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))
            else:
                state["errors"].append(f"Summarization failed: {result.error}")
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.SUMMARIZE,
                    status=TaskStatus.FAILED,
                    error=result.error,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))

        except Exception as e:
            logger.exception("Summarization node failed")
            state["errors"].append(f"Summarization error: {str(e)}")
            state["task_history"].append(TaskResult(
                task=ProcessingTask.SUMMARIZE,
                status=TaskStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))

        return state

    async def _detect_intent_node(self, state: WorkflowState) -> WorkflowState:
        """Execute intent detection."""
        logger.info("Executing intent detection task")
        started_at = datetime.utcnow()

        transcript_text = state.get("transcript_text")
        if not transcript_text:
            state["task_history"].append(TaskResult(
                task=ProcessingTask.DETECT_INTENT,
                status=TaskStatus.SKIPPED,
                data={"reason": "No transcript available"},
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))
            return state

        try:
            result = await self.intent_agent.execute(
                text=transcript_text,
                transcript_id=state.get("transcript_id"),
            )

            if result.success:
                state["intent_result"] = result.data
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.DETECT_INTENT,
                    status=TaskStatus.COMPLETED,
                    data=result.data,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))
            else:
                state["errors"].append(f"Intent detection failed: {result.error}")
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.DETECT_INTENT,
                    status=TaskStatus.FAILED,
                    error=result.error,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))

        except Exception as e:
            logger.exception("Intent detection node failed")
            state["errors"].append(f"Intent detection error: {str(e)}")
            state["task_history"].append(TaskResult(
                task=ProcessingTask.DETECT_INTENT,
                status=TaskStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))

        return state

    async def _extract_keywords_node(self, state: WorkflowState) -> WorkflowState:
        """Execute keyword extraction."""
        logger.info("Executing keyword extraction task")
        started_at = datetime.utcnow()

        transcript_text = state.get("transcript_text")
        if not transcript_text:
            state["task_history"].append(TaskResult(
                task=ProcessingTask.EXTRACT_KEYWORDS,
                status=TaskStatus.SKIPPED,
                data={"reason": "No transcript available"},
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))
            return state

        try:
            result = await self.keyword_agent.execute(
                text=transcript_text,
                transcript_id=state.get("transcript_id"),
                max_keywords=state.get("max_keywords", 20),
            )

            if result.success:
                state["keyword_result"] = result.data
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.EXTRACT_KEYWORDS,
                    status=TaskStatus.COMPLETED,
                    data=result.data,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))
            else:
                state["errors"].append(f"Keyword extraction failed: {result.error}")
                state["task_history"].append(TaskResult(
                    task=ProcessingTask.EXTRACT_KEYWORDS,
                    status=TaskStatus.FAILED,
                    error=result.error,
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                ))

        except Exception as e:
            logger.exception("Keyword extraction node failed")
            state["errors"].append(f"Keyword extraction error: {str(e)}")
            state["task_history"].append(TaskResult(
                task=ProcessingTask.EXTRACT_KEYWORDS,
                status=TaskStatus.FAILED,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow(),
            ))

        return state

    def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """Finalize the workflow and calculate metrics."""
        logger.info("Finalizing workflow")

        started_at = datetime.fromisoformat(state["started_at"])
        completed_at = datetime.utcnow()

        state["completed_at"] = completed_at.isoformat()
        state["total_duration_seconds"] = (completed_at - started_at).total_seconds()

        # Log summary
        completed_tasks = [
            r.task.value for r in state["task_history"]
            if r.status == TaskStatus.COMPLETED
        ]
        failed_tasks = [
            r.task.value for r in state["task_history"]
            if r.status == TaskStatus.FAILED
        ]

        logger.info(
            f"Workflow completed. Tasks completed: {completed_tasks}, "
            f"Failed: {failed_tasks}, Duration: {state['total_duration_seconds']:.2f}s"
        )

        return state

    async def process(
        self,
        audio_file_path: str,
        tasks: List[ProcessingTask],
        audio_file_id: Optional[int] = None,
        source_language: str = "en",
        target_languages: Optional[List[str]] = None,
        include_timestamps: bool = False,
        summary_type: str = "general",
        max_keywords: int = 20,
    ) -> Dict[str, Any]:
        """
        Process an audio file through the specified tasks.

        Args:
            audio_file_path: Path to the audio file
            tasks: List of processing tasks to execute
            audio_file_id: Optional database ID
            source_language: Source language code
            target_languages: List of target language codes for translation
            include_timestamps: Include word timestamps in transcription
            summary_type: Type of summary (general, key_points, action_items, quick)
            max_keywords: Maximum keywords to extract

        Returns:
            Final workflow state as a dictionary
        """
        # Create initial state
        initial_state = create_initial_state(
            audio_file_path=audio_file_path,
            tasks=tasks,
            audio_file_id=audio_file_id,
            source_language=source_language,
            target_languages=target_languages,
            include_timestamps=include_timestamps,
            summary_type=summary_type,
            max_keywords=max_keywords,
        )

        # Run the workflow
        final_state = await self.graph.ainvoke(initial_state)

        return dict(final_state)

    async def process_full_pipeline(
        self,
        audio_file_path: str,
        audio_file_id: Optional[int] = None,
        target_languages: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full processing pipeline on an audio file.

        This is a convenience method that runs all tasks:
        transcription, translation, summarization, intent detection, and keyword extraction.
        """
        return await self.process(
            audio_file_path=audio_file_path,
            tasks=[ProcessingTask.FULL_PIPELINE],
            audio_file_id=audio_file_id,
            target_languages=target_languages or [],
        )
