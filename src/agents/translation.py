"""Translation Agent for translating transcripts to other languages."""

from typing import Optional, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.agents.base import BaseAgent, AgentResult


# Language code to name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "pl": "Polish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "cs": "Czech",
    "el": "Greek",
    "he": "Hebrew",
    "hu": "Hungarian",
    "ro": "Romanian",
    "uk": "Ukrainian",
}


class TranslationAgent(BaseAgent):
    """Agent responsible for translating transcripts to other languages."""

    def __init__(self, **kwargs):
        super().__init__(
            name="translation_agent",
            description="Translates transcripts to other languages using LLM",
            **kwargs,
        )
        self._setup_chain()

    def _get_task_type(self) -> str:
        return "translation"

    def _setup_chain(self) -> None:
        """Set up the translation chain."""
        self.translation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional translator. Translate the following text
from {source_language} to {target_language}.

Guidelines:
- Maintain the original meaning and tone
- Preserve any technical terms appropriately
- Keep proper nouns as they are unless they have standard translations
- Maintain paragraph structure and formatting
- If there are idioms, translate them to equivalent expressions in the target language"""),
            ("human", "{text}"),
        ])

        self.translation_chain = (
            self.translation_prompt
            | self.llm
            | StrOutputParser()
        )

    async def execute(
        self,
        text: str,
        target_language: str,
        source_language: str = "en",
        transcript_id: Optional[int] = None,
    ) -> AgentResult:
        """
        Translate text to a target language.

        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            source_language: Source language code (default: 'en')
            transcript_id: Optional database ID of the transcript

        Returns:
            AgentResult with translation data
        """
        self._log_start(
            "translation",
            source_language=source_language,
            target_language=target_language,
            text_length=len(text),
        )

        try:
            # Validate languages
            source_name = LANGUAGE_NAMES.get(source_language, source_language)
            target_name = LANGUAGE_NAMES.get(target_language, target_language)

            if source_language == target_language:
                return self._create_error_result(
                    "Source and target languages are the same"
                )

            # Perform translation
            translated_text = await self.translation_chain.ainvoke({
                "text": text,
                "source_language": source_name,
                "target_language": target_name,
            })

            # Save to database if transcript_id provided
            db_result = None
            if transcript_id:
                db_result = await self.db_tools.create_translation(
                    transcript_id=transcript_id,
                    target_language=target_language,
                    translated_text=translated_text,
                    model_used=str(self.llm.model) if hasattr(self.llm, 'model') else "unknown",
                )

            result_data = {
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "source_word_count": len(text.split()),
                "translated_word_count": len(translated_text.split()),
            }

            if db_result:
                result_data["translation_id"] = db_result["id"]

            agent_result = self._create_success_result(data=result_data)
            self._log_complete("translation", agent_result)
            return agent_result

        except Exception as e:
            self.logger.exception("Translation failed")
            return self._create_error_result(str(e))

    async def translate_to_multiple(
        self,
        text: str,
        target_languages: List[str],
        source_language: str = "en",
        transcript_id: Optional[int] = None,
    ) -> List[AgentResult]:
        """
        Translate text to multiple target languages.

        Args:
            text: Text to translate
            target_languages: List of target language codes
            source_language: Source language code
            transcript_id: Optional database ID of the transcript

        Returns:
            List of AgentResult for each translation
        """
        results = []
        for target_lang in target_languages:
            result = await self.execute(
                text=text,
                target_language=target_lang,
                source_language=source_language,
                transcript_id=transcript_id,
            )
            results.append(result)
        return results

    @staticmethod
    def get_supported_languages() -> dict:
        """Get dictionary of supported language codes and names."""
        return LANGUAGE_NAMES.copy()
