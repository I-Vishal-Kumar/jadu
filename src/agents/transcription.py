"""Transcription Agent for converting audio to text."""

import os
from pathlib import Path
from typing import Optional

import whisper
import whisper.audio
import torch
import numpy as np

from src.agents.base import BaseAgent, AgentResult
from src.config import settings


def _get_ffmpeg_path():
    """Get the FFmpeg executable path from imageio-ffmpeg."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"  # fallback to system ffmpeg


def _ensure_ffmpeg_in_path():
    """Ensure FFmpeg from imageio-ffmpeg is in the system PATH."""
    import logging
    import shutil
    import subprocess
    logger = logging.getLogger(__name__)

    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)

        # Add to PATH at the very beginning
        current_path = os.environ.get("PATH", "")
        if ffmpeg_dir not in current_path:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path
            logger.info(f"Added FFmpeg to PATH: {ffmpeg_dir}")

        # Also set FFMPEG_BINARY environment variable as a fallback
        os.environ["FFMPEG_BINARY"] = ffmpeg_path

        # Create a copy named 'ffmpeg.exe' in the same directory if needed
        # (imageio-ffmpeg has it named differently)
        ffmpeg_standard = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        if not os.path.exists(ffmpeg_standard) and os.path.exists(ffmpeg_path):
            try:
                shutil.copy2(ffmpeg_path, ffmpeg_standard)
                logger.info(f"Created ffmpeg.exe copy at: {ffmpeg_standard}")
            except Exception as copy_error:
                logger.warning(f"Could not create ffmpeg.exe copy: {copy_error}")

        # Verify ffmpeg is accessible
        try:
            result = subprocess.run(
                [ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"FFmpeg verified: {ffmpeg_path}")
            else:
                logger.warning(f"FFmpeg verification failed: {result.stderr}")
        except Exception as verify_error:
            logger.warning(f"Could not verify FFmpeg: {verify_error}")

        return ffmpeg_path
    except ImportError as e:
        logger.error(f"imageio-ffmpeg not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error setting FFmpeg path: {e}")
        return None


def _load_audio_with_ffmpeg(file_path: str, sr: int = 16000):
    """Load audio file using imageio-ffmpeg's bundled FFmpeg."""
    import subprocess
    import logging
    logger = logging.getLogger(__name__)

    ffmpeg_path = _get_ffmpeg_path()
    logger.info(f"Loading audio with FFmpeg: {ffmpeg_path}")

    cmd = [
        ffmpeg_path,
        "-nostdin",
        "-threads", "0",
        "-i", file_path,
        "-f", "s16le",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(sr),
        "-"
    ]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg error: {err.decode()}")

        # Convert to numpy array
        audio = np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
        return audio

    except FileNotFoundError:
        raise RuntimeError(
            f"FFmpeg not found at {ffmpeg_path}. "
            "Please install FFmpeg or ensure imageio-ffmpeg is properly installed."
        )


class TranscriptionAgent(BaseAgent):
    """Agent responsible for transcribing audio files to text."""

    def __init__(self, **kwargs):
        super().__init__(
            name="transcription_agent",
            description="Transcribes audio files to text using Whisper",
            **kwargs,
        )
        self._whisper_model = None
        # Ensure FFmpeg is available
        _ensure_ffmpeg_in_path()

    def _get_task_type(self) -> str:
        return "transcription"

    @property
    def whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            # Ensure FFmpeg is in PATH before loading model
            _ensure_ffmpeg_in_path()
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.logger.info(
                f"Loading Whisper model '{settings.whisper_model.value}' on {device}"
            )
            self._whisper_model = whisper.load_model(
                settings.whisper_model.value, device=device
            )
        return self._whisper_model

    async def execute(
        self,
        audio_file_path: str,
        audio_file_id: Optional[int] = None,
        language: Optional[str] = None,
        include_timestamps: bool = False,
    ) -> AgentResult:
        """
        Transcribe an audio file to text.

        Args:
            audio_file_path: Path to the audio file
            audio_file_id: Optional database ID of the audio file
            language: Optional language code (auto-detected if not provided)
            include_timestamps: Whether to include word-level timestamps

        Returns:
            AgentResult with transcription data
        """
        self._log_start(
            "transcription",
            audio_file_path=audio_file_path,
            language=language,
        )

        try:
            # Validate file exists
            if not Path(audio_file_path).exists():
                return self._create_error_result(f"Audio file not found: {audio_file_path}")

            # Transcribe using Whisper
            transcribe_options = {
                "fp16": torch.cuda.is_available(),
                "verbose": False,
            }

            if language:
                transcribe_options["language"] = language

            if include_timestamps:
                transcribe_options["word_timestamps"] = True

            # Load audio using our custom function that uses imageio-ffmpeg
            self.logger.info(f"Loading audio from: {audio_file_path}")
            audio = _load_audio_with_ffmpeg(audio_file_path, sr=16000)
            self.logger.info(f"Audio loaded, duration: {len(audio) / 16000:.2f}s")

            result = self.whisper_model.transcribe(audio, **transcribe_options)

            # Extract data
            transcription_data = {
                "text": result["text"].strip(),
                "language": result.get("language", language or "en"),
                "segments": result.get("segments", []),
            }

            # Extract word timestamps if available
            word_timestamps = None
            if include_timestamps and "segments" in result:
                word_timestamps = []
                for segment in result["segments"]:
                    if "words" in segment:
                        word_timestamps.extend(segment["words"])

            # Save to database if audio_file_id provided
            db_result = None
            if audio_file_id:
                db_result = await self.db_tools.create_transcript(
                    audio_file_id=audio_file_id,
                    text=transcription_data["text"],
                    language=transcription_data["language"],
                    word_timestamps=word_timestamps,
                    model_used=f"whisper-{settings.whisper_model.value}",
                )

            result_data = {
                "text": transcription_data["text"],
                "language": transcription_data["language"],
                "word_count": len(transcription_data["text"].split()),
                "segments_count": len(transcription_data["segments"]),
            }

            if db_result:
                result_data["transcript_id"] = db_result["id"]

            if word_timestamps:
                result_data["word_timestamps"] = word_timestamps

            agent_result = self._create_success_result(
                data=result_data,
                metadata={"model": f"whisper-{settings.whisper_model.value}"},
            )
            self._log_complete("transcription", agent_result)
            return agent_result

        except Exception as e:
            self.logger.exception("Transcription failed")
            return self._create_error_result(str(e))

    async def transcribe_batch(
        self,
        audio_files: list[dict],
        language: Optional[str] = None,
    ) -> list[AgentResult]:
        """
        Transcribe multiple audio files.

        Args:
            audio_files: List of dicts with 'path' and optional 'id' keys
            language: Optional language code for all files

        Returns:
            List of AgentResult for each file
        """
        results = []
        for audio_file in audio_files:
            result = await self.execute(
                audio_file_path=audio_file["path"],
                audio_file_id=audio_file.get("id"),
                language=language,
            )
            results.append(result)
        return results
