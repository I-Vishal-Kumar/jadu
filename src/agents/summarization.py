"""Summarization Agent for creating summaries of transcripts."""

from typing import Optional, List, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, AgentResult


class SummaryOutput(BaseModel):
    """Structured output for summary generation."""

    summary: str = Field(description="A concise summary of the transcript")
    key_points: List[str] = Field(description="List of key points from the transcript")
    main_topics: List[str] = Field(description="Main topics discussed")
    action_items: Optional[List[str]] = Field(
        default=None, description="Action items if any are mentioned"
    )


class SummarizationAgent(BaseAgent):
    """Agent responsible for summarizing transcripts."""

    def __init__(self, **kwargs):
        super().__init__(
            name="summarization_agent",
            description="Creates summaries and extracts key points from transcripts",
            **kwargs,
        )
        self._setup_chains()

    def _get_task_type(self) -> str:
        return "summarization"

    def _setup_chains(self) -> None:
        """Set up the summarization chains."""
        self.output_parser = JsonOutputParser(pydantic_object=SummaryOutput)

        # General summary prompt
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing and summarizing spoken content.
Analyze the following transcript and provide a structured summary.

{format_instructions}

Guidelines:
- Keep the summary concise but comprehensive (2-4 paragraphs)
- Extract 3-7 key points that capture the main ideas
- Identify 2-5 main topics discussed
- If action items are mentioned, list them; otherwise, set action_items to null
- Maintain objectivity and accuracy"""),
            ("human", "Transcript:\n{text}"),
        ])

        self.summary_chain = (
            self.summary_prompt
            | self.llm
            | self.output_parser
        )

        # Quick summary prompt (shorter output)
        self.quick_summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """Provide a brief 1-2 sentence summary of the following transcript.
Focus on the main point or purpose."""),
            ("human", "{text}"),
        ])

    async def execute(
        self,
        text: str,
        summary_type: Literal["general", "key_points", "action_items", "quick"] = "general",
        transcript_id: Optional[int] = None,
    ) -> AgentResult:
        """
        Generate a summary of the transcript.

        Args:
            text: Transcript text to summarize
            summary_type: Type of summary to generate
            transcript_id: Optional database ID of the transcript

        Returns:
            AgentResult with summary data
        """
        self._log_start(
            "summarization",
            summary_type=summary_type,
            text_length=len(text),
        )

        try:
            if not text or len(text.strip()) < 10:
                return self._create_error_result("Text is too short to summarize")

            # Generate summary based on type
            if summary_type == "quick":
                from langchain_core.output_parsers import StrOutputParser
                quick_chain = self.quick_summary_prompt | self.llm | StrOutputParser()
                summary_text = await quick_chain.ainvoke({"text": text})
                result_data = {
                    "summary": summary_text,
                    "summary_type": "quick",
                }
            else:
                format_instructions = self.output_parser.get_format_instructions()
                summary_output = await self.summary_chain.ainvoke({
                    "text": text,
                    "format_instructions": format_instructions,
                })

                result_data = {
                    "summary": summary_output["summary"],
                    "key_points": summary_output["key_points"],
                    "main_topics": summary_output["main_topics"],
                    "action_items": summary_output.get("action_items"),
                    "summary_type": summary_type,
                }

            # Save to database if transcript_id provided
            if transcript_id:
                db_result = await self.db_tools.create_summary(
                    transcript_id=transcript_id,
                    summary_text=result_data["summary"],
                    summary_type=summary_type,
                    key_points=result_data.get("key_points"),
                    model_used=str(self.llm.model) if hasattr(self.llm, 'model') else "unknown",
                )
                result_data["summary_id"] = db_result["id"]

            agent_result = self._create_success_result(data=result_data)
            self._log_complete("summarization", agent_result)
            return agent_result

        except Exception as e:
            self.logger.exception("Summarization failed")
            return self._create_error_result(str(e))

    async def compare_summaries(
        self,
        texts: List[str],
    ) -> AgentResult:
        """
        Generate and compare summaries across multiple transcripts.

        Args:
            texts: List of transcript texts

        Returns:
            AgentResult with comparative analysis
        """
        self._log_start("compare_summaries", text_count=len(texts))

        try:
            # Generate summaries for all texts
            summaries = []
            for i, text in enumerate(texts):
                result = await self.execute(text, summary_type="general")
                if result.success:
                    summaries.append({
                        "index": i,
                        "summary": result.data["summary"],
                        "key_points": result.data.get("key_points", []),
                        "main_topics": result.data.get("main_topics", []),
                    })

            # Create comparison
            all_topics = []
            all_key_points = []
            for s in summaries:
                all_topics.extend(s.get("main_topics", []))
                all_key_points.extend(s.get("key_points", []))

            # Find common themes
            topic_counts = {}
            for topic in all_topics:
                topic_lower = topic.lower()
                topic_counts[topic_lower] = topic_counts.get(topic_lower, 0) + 1

            common_topics = [
                topic for topic, count in topic_counts.items()
                if count > 1
            ]

            result_data = {
                "individual_summaries": summaries,
                "common_topics": common_topics,
                "total_transcripts": len(texts),
                "total_key_points": len(all_key_points),
            }

            return self._create_success_result(data=result_data)

        except Exception as e:
            self.logger.exception("Compare summaries failed")
            return self._create_error_result(str(e))
