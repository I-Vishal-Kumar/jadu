"""Database tools for MCP server integration."""

from datetime import datetime
from typing import Any, Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from src.database.models import (
    AudioFile,
    Transcript,
    Translation,
    Summary,
    Intent,
    Keyword,
    ProcessingStatus,
    IntentCategory,
)
from src.database.connection import get_db_manager


class DatabaseTools:
    """Database operations exposed as MCP tools."""

    def __init__(self):
        self.db_manager = get_db_manager()

    # ==================== Audio File Operations ====================

    async def create_audio_file(
        self,
        filename: str,
        file_path: str,
        file_size_bytes: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        format: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        extra_data: Optional[dict] = None,
    ) -> dict:
        """Create a new audio file record in the database."""
        async with self.db_manager.get_session() as session:
            audio_file = AudioFile(
                filename=filename,
                file_path=file_path,
                file_size_bytes=file_size_bytes,
                duration_seconds=duration_seconds,
                format=format,
                sample_rate=sample_rate,
                channels=channels,
                status=ProcessingStatus.PENDING,
                extra_data=extra_data,
            )
            session.add(audio_file)
            await session.flush()
            return {
                "id": audio_file.id,
                "filename": audio_file.filename,
                "file_path": audio_file.file_path,
                "status": audio_file.status.value,
            }

    async def get_audio_file(self, audio_file_id: int) -> Optional[dict]:
        """Get an audio file by ID with all related data."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(AudioFile)
                .options(
                    selectinload(AudioFile.transcript).selectinload(Transcript.translations),
                    selectinload(AudioFile.transcript).selectinload(Transcript.summaries),
                    selectinload(AudioFile.transcript).selectinload(Transcript.intents),
                    selectinload(AudioFile.transcript).selectinload(Transcript.keywords),
                )
                .where(AudioFile.id == audio_file_id)
            )
            audio_file = result.scalar_one_or_none()
            if not audio_file:
                return None
            return self._serialize_audio_file(audio_file)

    async def list_audio_files(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """List audio files with optional filtering."""
        async with self.db_manager.get_session() as session:
            query = select(AudioFile).limit(limit).offset(offset)
            if status:
                query = query.where(AudioFile.status == ProcessingStatus(status))
            result = await session.execute(query.order_by(AudioFile.created_at.desc()))
            audio_files = result.scalars().all()
            return [self._serialize_audio_file(af, include_relations=False) for af in audio_files]

    async def update_audio_file_status(
        self, audio_file_id: int, status: str
    ) -> dict:
        """Update the processing status of an audio file."""
        async with self.db_manager.get_session() as session:
            await session.execute(
                update(AudioFile)
                .where(AudioFile.id == audio_file_id)
                .values(status=ProcessingStatus(status), updated_at=datetime.utcnow())
            )
            return {"id": audio_file_id, "status": status, "updated": True}

    async def delete_audio_file(self, audio_file_id: int) -> dict:
        """Delete an audio file and all related data."""
        async with self.db_manager.get_session() as session:
            await session.execute(delete(AudioFile).where(AudioFile.id == audio_file_id))
            return {"id": audio_file_id, "deleted": True}

    # ==================== Transcript Operations ====================

    async def create_transcript(
        self,
        audio_file_id: int,
        text: str,
        language: str = "en",
        confidence: Optional[float] = None,
        word_timestamps: Optional[dict] = None,
        model_used: Optional[str] = None,
    ) -> dict:
        """Create a new transcript for an audio file."""
        async with self.db_manager.get_session() as session:
            transcript = Transcript(
                audio_file_id=audio_file_id,
                text=text,
                language=language,
                confidence=confidence,
                word_timestamps=word_timestamps,
                model_used=model_used,
            )
            session.add(transcript)
            await session.flush()

            # Update audio file status
            await session.execute(
                update(AudioFile)
                .where(AudioFile.id == audio_file_id)
                .values(status=ProcessingStatus.COMPLETED, updated_at=datetime.utcnow())
            )

            return {
                "id": transcript.id,
                "audio_file_id": audio_file_id,
                "language": language,
                "text_length": len(text),
            }

    async def get_transcript(self, transcript_id: int) -> Optional[dict]:
        """Get a transcript by ID."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Transcript).where(Transcript.id == transcript_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript:
                return None
            return self._serialize_transcript(transcript)

    async def get_transcript_by_audio_file(self, audio_file_id: int) -> Optional[dict]:
        """Get transcript by audio file ID."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Transcript).where(Transcript.audio_file_id == audio_file_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript:
                return None
            return self._serialize_transcript(transcript)

    # ==================== Translation Operations ====================

    async def create_translation(
        self,
        transcript_id: int,
        target_language: str,
        translated_text: str,
        model_used: Optional[str] = None,
    ) -> dict:
        """Create a new translation for a transcript."""
        async with self.db_manager.get_session() as session:
            translation = Translation(
                transcript_id=transcript_id,
                target_language=target_language,
                translated_text=translated_text,
                model_used=model_used,
            )
            session.add(translation)
            await session.flush()
            return {
                "id": translation.id,
                "transcript_id": transcript_id,
                "target_language": target_language,
                "text_length": len(translated_text),
            }

    async def get_translations(self, transcript_id: int) -> List[dict]:
        """Get all translations for a transcript."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Translation).where(Translation.transcript_id == transcript_id)
            )
            translations = result.scalars().all()
            return [
                {
                    "id": t.id,
                    "target_language": t.target_language,
                    "translated_text": t.translated_text,
                    "model_used": t.model_used,
                    "created_at": t.created_at.isoformat(),
                }
                for t in translations
            ]

    # ==================== Summary Operations ====================

    async def create_summary(
        self,
        transcript_id: int,
        summary_text: str,
        summary_type: str = "general",
        key_points: Optional[list] = None,
        model_used: Optional[str] = None,
    ) -> dict:
        """Create a new summary for a transcript."""
        async with self.db_manager.get_session() as session:
            summary = Summary(
                transcript_id=transcript_id,
                summary_text=summary_text,
                summary_type=summary_type,
                key_points=key_points,
                model_used=model_used,
            )
            session.add(summary)
            await session.flush()
            return {
                "id": summary.id,
                "transcript_id": transcript_id,
                "summary_type": summary_type,
                "text_length": len(summary_text),
            }

    async def get_summaries(self, transcript_id: int) -> List[dict]:
        """Get all summaries for a transcript."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Summary).where(Summary.transcript_id == transcript_id)
            )
            summaries = result.scalars().all()
            return [
                {
                    "id": s.id,
                    "summary_type": s.summary_type,
                    "summary_text": s.summary_text,
                    "key_points": s.key_points,
                    "model_used": s.model_used,
                    "created_at": s.created_at.isoformat(),
                }
                for s in summaries
            ]

    # ==================== Intent Operations ====================

    async def create_intent(
        self,
        transcript_id: int,
        category: str,
        confidence: float,
        reasoning: Optional[str] = None,
        sub_intents: Optional[list] = None,
        model_used: Optional[str] = None,
    ) -> dict:
        """Create a new intent classification for a transcript."""
        async with self.db_manager.get_session() as session:
            intent = Intent(
                transcript_id=transcript_id,
                category=IntentCategory(category),
                confidence=confidence,
                reasoning=reasoning,
                sub_intents=sub_intents,
                model_used=model_used,
            )
            session.add(intent)
            await session.flush()
            return {
                "id": intent.id,
                "transcript_id": transcript_id,
                "category": category,
                "confidence": confidence,
            }

    async def get_intents(self, transcript_id: int) -> List[dict]:
        """Get all intent classifications for a transcript."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Intent).where(Intent.transcript_id == transcript_id)
            )
            intents = result.scalars().all()
            return [
                {
                    "id": i.id,
                    "category": i.category.value,
                    "confidence": i.confidence,
                    "reasoning": i.reasoning,
                    "sub_intents": i.sub_intents,
                    "model_used": i.model_used,
                    "created_at": i.created_at.isoformat(),
                }
                for i in intents
            ]

    # ==================== Keyword Operations ====================

    async def create_keywords(
        self,
        transcript_id: int,
        keywords: List[dict],
    ) -> dict:
        """Create multiple keywords for a transcript."""
        async with self.db_manager.get_session() as session:
            keyword_objects = []
            for kw in keywords:
                keyword = Keyword(
                    transcript_id=transcript_id,
                    keyword=kw["keyword"],
                    keyword_type=kw.get("type", "keyword"),
                    relevance_score=kw.get("relevance_score"),
                    frequency=kw.get("frequency"),
                    context=kw.get("context"),
                )
                keyword_objects.append(keyword)
            session.add_all(keyword_objects)
            await session.flush()
            return {
                "transcript_id": transcript_id,
                "keywords_created": len(keywords),
            }

    async def get_keywords(self, transcript_id: int) -> List[dict]:
        """Get all keywords for a transcript."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Keyword)
                .where(Keyword.transcript_id == transcript_id)
                .order_by(Keyword.relevance_score.desc())
            )
            keywords = result.scalars().all()
            return [
                {
                    "id": k.id,
                    "keyword": k.keyword,
                    "type": k.keyword_type,
                    "relevance_score": k.relevance_score,
                    "frequency": k.frequency,
                    "context": k.context,
                }
                for k in keywords
            ]

    # ==================== Search Operations ====================

    async def search_transcripts(self, query: str, limit: int = 20) -> List[dict]:
        """Search transcripts containing the query text."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Transcript)
                .where(Transcript.text.contains(query))
                .limit(limit)
            )
            transcripts = result.scalars().all()
            return [self._serialize_transcript(t) for t in transcripts]

    async def get_transcripts_by_intent(
        self, category: str, min_confidence: float = 0.5
    ) -> List[dict]:
        """Get transcripts by intent category."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(Intent)
                .where(
                    Intent.category == IntentCategory(category),
                    Intent.confidence >= min_confidence,
                )
                .options(selectinload(Intent.transcript))
            )
            intents = result.scalars().all()
            return [
                {
                    "intent": {
                        "category": i.category.value,
                        "confidence": i.confidence,
                    },
                    "transcript": self._serialize_transcript(i.transcript),
                }
                for i in intents
            ]

    # ==================== Helper Methods ====================

    def _serialize_audio_file(
        self, audio_file: AudioFile, include_relations: bool = True
    ) -> dict:
        """Serialize an AudioFile object to dict."""
        data = {
            "id": audio_file.id,
            "filename": audio_file.filename,
            "file_path": audio_file.file_path,
            "file_size_bytes": audio_file.file_size_bytes,
            "duration_seconds": audio_file.duration_seconds,
            "format": audio_file.format,
            "sample_rate": audio_file.sample_rate,
            "channels": audio_file.channels,
            "status": audio_file.status.value,
            "created_at": audio_file.created_at.isoformat(),
            "updated_at": audio_file.updated_at.isoformat(),
            "extra_data": audio_file.extra_data,
        }
        if include_relations and audio_file.transcript:
            data["transcript"] = self._serialize_transcript(audio_file.transcript)
        return data

    def _serialize_transcript(self, transcript: Transcript) -> dict:
        """Serialize a Transcript object to dict."""
        return {
            "id": transcript.id,
            "audio_file_id": transcript.audio_file_id,
            "text": transcript.text,
            "language": transcript.language,
            "confidence": transcript.confidence,
            "model_used": transcript.model_used,
            "created_at": transcript.created_at.isoformat(),
        }
