"""LangChain tool implementations for the audio transcription system."""

import asyncio
from typing import List, Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.agents import (
    TranscriptionAgent,
    TranslationAgent,
    SummarizationAgent,
    IntentDetectionAgent,
    KeywordExtractionAgent,
)
from src.orchestrator import AudioTranscriptionOrchestrator, ProcessingTask


class TranscribeInput(BaseModel):
    """Input schema for transcription tool."""

    audio_file_path: str = Field(description="Path to the audio file to transcribe")
    language: Optional[str] = Field(
        default=None, description="Language code (e.g., 'en', 'es'). Auto-detected if not provided."
    )
    include_timestamps: bool = Field(
        default=False, description="Whether to include word-level timestamps"
    )


class TranscribeAudioTool(BaseTool):
    """Tool for transcribing audio files to text."""

    name: str = "transcribe_audio"
    description: str = """Transcribe an audio file to text using Whisper.
    Supports various audio formats (mp3, wav, flac, m4a, etc.).
    Can auto-detect the language or use a specified language code.
    Returns the transcribed text along with detected language and word count."""
    args_schema: Type[BaseModel] = TranscribeInput

    def _run(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        include_timestamps: bool = False,
    ) -> str:
        """Synchronous run method."""
        return asyncio.run(
            self._arun(audio_file_path, language, include_timestamps)
        )

    async def _arun(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        include_timestamps: bool = False,
    ) -> str:
        """Async run method."""
        agent = TranscriptionAgent()
        result = await agent.execute(
            audio_file_path=audio_file_path,
            language=language,
            include_timestamps=include_timestamps,
        )

        if result.success:
            return f"Transcription successful.\nLanguage: {result.data['language']}\nWord count: {result.data['word_count']}\n\nText:\n{result.data['text']}"
        else:
            return f"Transcription failed: {result.error}"


class TranslateInput(BaseModel):
    """Input schema for translation tool."""

    text: str = Field(description="Text to translate")
    target_language: str = Field(
        description="Target language code (e.g., 'es' for Spanish, 'fr' for French)"
    )
    source_language: str = Field(
        default="en", description="Source language code"
    )


class TranslateTextTool(BaseTool):
    """Tool for translating text to other languages."""

    name: str = "translate_text"
    description: str = """Translate text from one language to another.
    Supports many language pairs including English, Spanish, French, German, Chinese, Japanese, and more.
    Returns the translated text."""
    args_schema: Type[BaseModel] = TranslateInput

    def _run(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
    ) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(text, target_language, source_language))

    async def _arun(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
    ) -> str:
        """Async run method."""
        agent = TranslationAgent()
        result = await agent.execute(
            text=text,
            target_language=target_language,
            source_language=source_language,
        )

        if result.success:
            return f"Translation ({source_language} -> {target_language}):\n\n{result.data['translated_text']}"
        else:
            return f"Translation failed: {result.error}"


class SummarizeInput(BaseModel):
    """Input schema for summarization tool."""

    text: str = Field(description="Text to summarize")
    summary_type: str = Field(
        default="general",
        description="Type of summary: 'general', 'key_points', 'action_items', or 'quick'",
    )


class SummarizeTextTool(BaseTool):
    """Tool for summarizing text content."""

    name: str = "summarize_text"
    description: str = """Create a summary of text content.
    Can generate different types of summaries:
    - general: Comprehensive summary with key points and topics
    - key_points: Focus on extracting key points
    - action_items: Focus on actionable items
    - quick: Brief 1-2 sentence summary
    Returns the summary along with key points and main topics."""
    args_schema: Type[BaseModel] = SummarizeInput

    def _run(
        self,
        text: str,
        summary_type: str = "general",
    ) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(text, summary_type))

    async def _arun(
        self,
        text: str,
        summary_type: str = "general",
    ) -> str:
        """Async run method."""
        agent = SummarizationAgent()
        result = await agent.execute(text=text, summary_type=summary_type)

        if result.success:
            output = f"Summary ({summary_type}):\n\n{result.data['summary']}"
            if result.data.get("key_points"):
                output += "\n\nKey Points:"
                for point in result.data["key_points"]:
                    output += f"\n• {point}"
            if result.data.get("main_topics"):
                output += f"\n\nMain Topics: {', '.join(result.data['main_topics'])}"
            return output
        else:
            return f"Summarization failed: {result.error}"


class DetectIntentInput(BaseModel):
    """Input schema for intent detection tool."""

    text: str = Field(description="Text to analyze for intent")


class DetectIntentTool(BaseTool):
    """Tool for detecting intent in text."""

    name: str = "detect_intent"
    description: str = """Detect and classify the intent of text content.
    Categorizes content into intents like: inquiry, complaint, feedback, request, information, support, sales, or other.
    Also provides sentiment analysis (positive/negative/neutral) and urgency level (low/medium/high).
    Returns the primary intent, confidence score, and reasoning."""
    args_schema: Type[BaseModel] = DetectIntentInput

    def _run(self, text: str) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(text))

    async def _arun(self, text: str) -> str:
        """Async run method."""
        agent = IntentDetectionAgent()
        result = await agent.execute(text=text)

        if result.success:
            data = result.data
            return f"""Intent Detection Results:
Primary Intent: {data['primary_intent']}
Confidence: {data['confidence']:.1%}
Sentiment: {data['sentiment']}
Urgency: {data['urgency']}
Reasoning: {data['reasoning']}
Secondary Intents: {', '.join(data.get('secondary_intents', [])) or 'None'}"""
        else:
            return f"Intent detection failed: {result.error}"


class ExtractKeywordsInput(BaseModel):
    """Input schema for keyword extraction tool."""

    text: str = Field(description="Text to extract keywords from")
    max_keywords: int = Field(
        default=20, description="Maximum number of keywords to extract"
    )


class ExtractKeywordsTool(BaseTool):
    """Tool for extracting keywords and keyphrases from text."""

    name: str = "extract_keywords"
    description: str = """Extract keywords, keyphrases, and named entities from text.
    Identifies important terms including single keywords, multi-word keyphrases, and named entities (people, organizations, products, etc.).
    Returns keywords with relevance scores and the main theme/domain of the content."""
    args_schema: Type[BaseModel] = ExtractKeywordsInput

    def _run(
        self,
        text: str,
        max_keywords: int = 20,
    ) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(text, max_keywords))

    async def _arun(
        self,
        text: str,
        max_keywords: int = 20,
    ) -> str:
        """Async run method."""
        agent = KeywordExtractionAgent()
        result = await agent.execute(text=text, max_keywords=max_keywords)

        if result.success:
            data = result.data
            output = f"""Keyword Extraction Results:
Main Theme: {data['main_theme']}
Domain: {data['domain']}
Total Keywords: {data['total_extracted']}

Keywords:"""
            for kw in data["keywords"][:15]:
                output += f"\n• {kw['keyword']} ({kw['type']}, score: {kw['relevance_score']:.2f})"
            return output
        else:
            return f"Keyword extraction failed: {result.error}"


class FullPipelineInput(BaseModel):
    """Input schema for full pipeline tool."""

    audio_file_path: str = Field(description="Path to the audio file to process")
    target_languages: Optional[List[str]] = Field(
        default=None,
        description="Optional list of language codes to translate to (e.g., ['es', 'fr'])",
    )


class FullPipelineTool(BaseTool):
    """Tool for running the full audio processing pipeline."""

    name: str = "audio_full_pipeline"
    description: str = """Process an audio file through the complete analysis pipeline.
    This includes:
    1. Transcription: Convert audio to text
    2. Translation: Translate to specified languages (optional)
    3. Summarization: Generate summary and key points
    4. Intent Detection: Classify the intent and sentiment
    5. Keyword Extraction: Extract important terms and topics

    Returns comprehensive analysis results for the audio content."""
    args_schema: Type[BaseModel] = FullPipelineInput

    def _run(
        self,
        audio_file_path: str,
        target_languages: Optional[List[str]] = None,
    ) -> str:
        """Synchronous run method."""
        return asyncio.run(self._arun(audio_file_path, target_languages))

    async def _arun(
        self,
        audio_file_path: str,
        target_languages: Optional[List[str]] = None,
    ) -> str:
        """Async run method."""
        orchestrator = AudioTranscriptionOrchestrator()
        result = await orchestrator.process_full_pipeline(
            audio_file_path=audio_file_path,
            target_languages=target_languages or [],
        )

        output = ["=" * 50, "FULL PIPELINE RESULTS", "=" * 50]

        # Transcription
        if result.get("transcription_result"):
            tr = result["transcription_result"]
            output.append(f"\n📝 TRANSCRIPTION:")
            output.append(f"Language: {tr.get('language')}")
            output.append(f"Words: {tr.get('word_count')}")
            text = tr.get("text", "")
            output.append(f"Text: {text[:500]}{'...' if len(text) > 500 else ''}")

        # Summary
        if result.get("summary_result"):
            sr = result["summary_result"]
            output.append(f"\n📋 SUMMARY:")
            output.append(sr.get("summary", ""))

        # Intent
        if result.get("intent_result"):
            ir = result["intent_result"]
            output.append(f"\n🎯 INTENT: {ir.get('primary_intent')} ({ir.get('confidence', 0):.0%})")
            output.append(f"Sentiment: {ir.get('sentiment')} | Urgency: {ir.get('urgency')}")

        # Keywords
        if result.get("keyword_result"):
            kr = result["keyword_result"]
            keywords = [kw["keyword"] for kw in kr.get("keywords", [])[:10]]
            output.append(f"\n🔑 KEYWORDS: {', '.join(keywords)}")

        # Errors
        if result.get("errors"):
            output.append(f"\n⚠️ ERRORS: {'; '.join(result['errors'])}")

        output.append(f"\n⏱️ Duration: {result.get('total_duration_seconds', 0):.2f}s")

        return "\n".join(output)


def get_all_tools() -> List[BaseTool]:
    """Get all available LangChain tools."""
    return [
        TranscribeAudioTool(),
        TranslateTextTool(),
        SummarizeTextTool(),
        DetectIntentTool(),
        ExtractKeywordsTool(),
        FullPipelineTool(),
    ]
