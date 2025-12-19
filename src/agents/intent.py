"""Intent Detection Agent for classifying transcript intents."""

from typing import Optional, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, AgentResult
from src.database.models import IntentCategory


class IntentOutput(BaseModel):
    """Structured output for intent detection."""

    primary_intent: str = Field(
        description="The primary intent category (inquiry, complaint, feedback, request, information, support, sales, other)"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0,
    )
    secondary_intents: List[str] = Field(
        default=[],
        description="List of secondary intents if applicable"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification"
    )
    sentiment: str = Field(
        description="Overall sentiment: positive, negative, neutral, or mixed"
    )
    urgency: str = Field(
        description="Urgency level: low, medium, high"
    )


class IntentDetectionAgent(BaseAgent):
    """Agent responsible for detecting and classifying intents in transcripts."""

    INTENT_CATEGORIES = [
        ("inquiry", "Questions seeking information or clarification"),
        ("complaint", "Expressions of dissatisfaction or problems"),
        ("feedback", "General feedback, opinions, or suggestions"),
        ("request", "Requests for action, service, or assistance"),
        ("information", "Sharing or providing information"),
        ("support", "Technical support or help-seeking"),
        ("sales", "Sales-related discussions, purchases, or negotiations"),
        ("other", "Content that doesn't fit other categories"),
    ]

    def __init__(self, **kwargs):
        super().__init__(
            name="intent_detection_agent",
            description="Detects and classifies intents in transcripts",
            **kwargs,
        )
        self._setup_chain()

    def _get_task_type(self) -> str:
        return "intent_detection"

    def _setup_chain(self) -> None:
        """Set up the intent detection chain."""
        self.output_parser = JsonOutputParser(pydantic_object=IntentOutput)

        categories_description = "\n".join([
            f"- {cat}: {desc}" for cat, desc in self.INTENT_CATEGORIES
        ])

        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing spoken content to detect intents and classify communications.

Analyze the following transcript and determine the intent behind it.

Available intent categories:
{categories}

{format_instructions}

Guidelines:
- Choose the most appropriate primary intent
- Provide a confidence score (0.0-1.0) based on how clearly the intent is expressed
- Identify any secondary intents if the content serves multiple purposes
- Explain your reasoning briefly
- Assess the overall sentiment and urgency level"""),
            ("human", "Transcript:\n{text}"),
        ])

        self.intent_chain = (
            self.intent_prompt
            | self.llm
            | self.output_parser
        )

    async def execute(
        self,
        text: str,
        transcript_id: Optional[int] = None,
    ) -> AgentResult:
        """
        Detect and classify the intent of a transcript.

        Args:
            text: Transcript text to analyze
            transcript_id: Optional database ID of the transcript

        Returns:
            AgentResult with intent classification data
        """
        self._log_start("intent_detection", text_length=len(text))

        try:
            if not text or len(text.strip()) < 5:
                return self._create_error_result("Text is too short to analyze")

            # Get format instructions
            format_instructions = self.output_parser.get_format_instructions()
            categories_desc = "\n".join([
                f"- {cat}: {desc}" for cat, desc in self.INTENT_CATEGORIES
            ])

            # Detect intent
            intent_output = await self.intent_chain.ainvoke({
                "text": text,
                "format_instructions": format_instructions,
                "categories": categories_desc,
            })

            # Validate primary intent
            primary_intent = intent_output["primary_intent"].lower()
            valid_intents = [cat for cat, _ in self.INTENT_CATEGORIES]
            if primary_intent not in valid_intents:
                primary_intent = "other"

            result_data = {
                "primary_intent": primary_intent,
                "confidence": intent_output["confidence"],
                "secondary_intents": intent_output.get("secondary_intents", []),
                "reasoning": intent_output["reasoning"],
                "sentiment": intent_output.get("sentiment", "neutral"),
                "urgency": intent_output.get("urgency", "medium"),
            }

            # Save to database if transcript_id provided
            if transcript_id:
                db_result = await self.db_tools.create_intent(
                    transcript_id=transcript_id,
                    category=primary_intent,
                    confidence=result_data["confidence"],
                    reasoning=result_data["reasoning"],
                    sub_intents=result_data["secondary_intents"],
                    model_used=str(self.llm.model) if hasattr(self.llm, 'model') else "unknown",
                )
                result_data["intent_id"] = db_result["id"]

            agent_result = self._create_success_result(data=result_data)
            self._log_complete("intent_detection", agent_result)
            return agent_result

        except Exception as e:
            self.logger.exception("Intent detection failed")
            return self._create_error_result(str(e))

    async def batch_classify(
        self,
        texts: List[str],
        transcript_ids: Optional[List[int]] = None,
    ) -> List[AgentResult]:
        """
        Classify intents for multiple transcripts.

        Args:
            texts: List of transcript texts
            transcript_ids: Optional list of database IDs

        Returns:
            List of AgentResult for each transcript
        """
        results = []
        for i, text in enumerate(texts):
            transcript_id = transcript_ids[i] if transcript_ids and i < len(transcript_ids) else None
            result = await self.execute(text=text, transcript_id=transcript_id)
            results.append(result)
        return results

    async def get_intent_distribution(
        self,
        texts: List[str],
    ) -> AgentResult:
        """
        Analyze intent distribution across multiple transcripts.

        Args:
            texts: List of transcript texts

        Returns:
            AgentResult with intent distribution analysis
        """
        self._log_start("intent_distribution", text_count=len(texts))

        try:
            # Classify all texts
            results = await self.batch_classify(texts)

            # Calculate distribution
            intent_counts = {}
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
            urgency_counts = {"low": 0, "medium": 0, "high": 0}
            total_confidence = 0
            success_count = 0

            for result in results:
                if result.success:
                    success_count += 1
                    intent = result.data["primary_intent"]
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
                    total_confidence += result.data["confidence"]

                    sentiment = result.data.get("sentiment", "neutral")
                    if sentiment in sentiment_counts:
                        sentiment_counts[sentiment] += 1

                    urgency = result.data.get("urgency", "medium")
                    if urgency in urgency_counts:
                        urgency_counts[urgency] += 1

            # Calculate percentages
            if success_count > 0:
                intent_distribution = {
                    intent: {
                        "count": count,
                        "percentage": round(count / success_count * 100, 2),
                    }
                    for intent, count in intent_counts.items()
                }
                avg_confidence = round(total_confidence / success_count, 3)
            else:
                intent_distribution = {}
                avg_confidence = 0

            result_data = {
                "total_analyzed": len(texts),
                "successful_analyses": success_count,
                "intent_distribution": intent_distribution,
                "sentiment_distribution": sentiment_counts,
                "urgency_distribution": urgency_counts,
                "average_confidence": avg_confidence,
            }

            return self._create_success_result(data=result_data)

        except Exception as e:
            self.logger.exception("Intent distribution analysis failed")
            return self._create_error_result(str(e))

    @staticmethod
    def get_available_intents() -> List[tuple]:
        """Get list of available intent categories."""
        return IntentDetectionAgent.INTENT_CATEGORIES.copy()
