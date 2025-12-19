"""SQLAlchemy models for the Audio Transcription Tool."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class ProcessingStatus(str, enum.Enum):
    """Status of audio processing."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IntentCategory(str, enum.Enum):
    """Categories for intent classification."""

    INQUIRY = "inquiry"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    REQUEST = "request"
    INFORMATION = "information"
    SUPPORT = "support"
    SALES = "sales"
    OTHER = "other"


class AudioFile(Base):
    """Model representing an audio file in the repository."""

    __tablename__ = "audio_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[ProcessingStatus] = mapped_column(
        SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    transcript: Mapped[Optional["Transcript"]] = relationship(
        "Transcript", back_populates="audio_file", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AudioFile(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class Transcript(Base):
    """Model representing a transcript of an audio file."""

    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audio_file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("audio_files.id"), nullable=False, unique=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="en")
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    word_timestamps: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    audio_file: Mapped["AudioFile"] = relationship("AudioFile", back_populates="transcript")
    translations: Mapped[List["Translation"]] = relationship(
        "Translation", back_populates="transcript", cascade="all, delete-orphan"
    )
    summaries: Mapped[List["Summary"]] = relationship(
        "Summary", back_populates="transcript", cascade="all, delete-orphan"
    )
    intents: Mapped[List["Intent"]] = relationship(
        "Intent", back_populates="transcript", cascade="all, delete-orphan"
    )
    keywords: Mapped[List["Keyword"]] = relationship(
        "Keyword", back_populates="transcript", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, audio_file_id={self.audio_file_id}, language='{self.language}')>"


class Translation(Base):
    """Model representing a translation of a transcript."""

    __tablename__ = "translations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcript_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripts.id"), nullable=False
    )
    target_language: Mapped[str] = mapped_column(String(50), nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="translations")

    def __repr__(self) -> str:
        return f"<Translation(id={self.id}, transcript_id={self.transcript_id}, language='{self.target_language}')>"


class Summary(Base):
    """Model representing a summary of a transcript."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcript_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripts.id"), nullable=False
    )
    summary_type: Mapped[str] = mapped_column(
        String(50), default="general"
    )  # general, key_points, action_items
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="summaries")

    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, transcript_id={self.transcript_id}, type='{self.summary_type}')>"


class Intent(Base):
    """Model representing detected intent from a transcript."""

    __tablename__ = "intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcript_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripts.id"), nullable=False
    )
    category: Mapped[IntentCategory] = mapped_column(SQLEnum(IntentCategory), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sub_intents: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="intents")

    def __repr__(self) -> str:
        return f"<Intent(id={self.id}, transcript_id={self.transcript_id}, category='{self.category}')>"


class Keyword(Base):
    """Model representing extracted keywords/keyphrases from a transcript."""

    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transcript_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripts.id"), nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(500), nullable=False)
    keyword_type: Mapped[str] = mapped_column(
        String(50), default="keyword"
    )  # keyword, keyphrase, entity
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    transcript: Mapped["Transcript"] = relationship("Transcript", back_populates="keywords")

    def __repr__(self) -> str:
        return f"<Keyword(id={self.id}, keyword='{self.keyword}', score={self.relevance_score})>"
