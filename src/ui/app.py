"""FastAPI application for the Audio Transcription UI."""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import settings
from src.database.connection import init_db, get_db_manager
from src.orchestrator import AudioTranscriptionOrchestrator, ProcessingTask
from src.agents import (
    TranslationAgent,
    SummarizationAgent,
    IntentDetectionAgent,
    KeywordExtractionAgent,
)

logger = logging.getLogger(__name__)

# Store active WebSocket connections and processing jobs
active_connections: Dict[str, WebSocket] = {}
processing_jobs: Dict[str, Dict[str, Any]] = {}


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # user or assistant
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class ProcessingRequest(BaseModel):
    """Request for processing text or audio."""
    text: Optional[str] = None
    audio_file_id: Optional[str] = None
    tasks: List[str] = ["summarize", "intent", "keywords"]
    target_languages: Optional[List[str]] = None


class TextAnalysisRequest(BaseModel):
    """Request for text analysis."""
    text: str
    tasks: List[str] = ["summarize", "intent", "keywords"]
    target_languages: Optional[List[str]] = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Audio Transcription & Intent Summary",
        description="AI-powered audio transcription with NLP analysis",
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure directories exist
    settings.ensure_directories()
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    @app.on_event("startup")
    async def startup():
        """Initialize on startup."""
        await init_db()
        logger.info("Application started")

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the main UI."""
        return get_html_template()

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "provider": settings.get_active_provider().value,
        }

    @app.post("/api/upload")
    async def upload_audio(file: UploadFile = File(...)):
        """Upload an audio file for processing."""
        # Validate file type
        allowed_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".webm"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = upload_dir / filename

        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path),
        }

    @app.post("/api/transcribe/{file_id}")
    async def transcribe_only(file_id: str):
        """Transcribe an audio file and return just the text."""
        from src.agents import TranscriptionAgent

        # Find the file
        file_path = None
        for ext in [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".webm"]:
            potential_path = upload_dir / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break

        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        try:
            agent = TranscriptionAgent()
            result = await agent.execute(audio_file_path=str(file_path))

            if result.success:
                return {
                    "success": True,
                    "text": result.data.get("text", ""),
                    "language": result.data.get("language", "en"),
                }
            else:
                raise HTTPException(status_code=500, detail=result.error or "Transcription failed")
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/process/audio/{file_id}")
    async def process_audio(
        file_id: str,
        tasks: List[str] = ["transcribe", "summarize", "intent", "keywords"],
        target_languages: Optional[List[str]] = None,
    ):
        """Process an uploaded audio file."""
        # Find the file
        file_path = None
        for ext in [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".webm"]:
            potential_path = upload_dir / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break

        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")

        # Map task names to ProcessingTask enum
        task_map = {
            "transcribe": ProcessingTask.TRANSCRIBE,
            "translate": ProcessingTask.TRANSLATE,
            "summarize": ProcessingTask.SUMMARIZE,
            "intent": ProcessingTask.DETECT_INTENT,
            "keywords": ProcessingTask.EXTRACT_KEYWORDS,
            "full": ProcessingTask.FULL_PIPELINE,
        }

        processing_tasks = [task_map[t] for t in tasks if t in task_map]

        # Process the audio
        orchestrator = AudioTranscriptionOrchestrator()
        result = await orchestrator.process(
            audio_file_path=str(file_path),
            tasks=processing_tasks,
            target_languages=target_languages or [],
        )

        # Format response
        return format_processing_result(result)

    @app.post("/api/analyze/text")
    async def analyze_text(request: TextAnalysisRequest):
        """Analyze text without audio transcription."""
        results = {}

        if "summarize" in request.tasks:
            agent = SummarizationAgent()
            result = await agent.execute(text=request.text, summary_type="general")
            if result.success:
                results["summary"] = result.data

        if "intent" in request.tasks:
            agent = IntentDetectionAgent()
            result = await agent.execute(text=request.text)
            if result.success:
                results["intent"] = result.data

        if "keywords" in request.tasks:
            agent = KeywordExtractionAgent()
            result = await agent.execute(text=request.text)
            if result.success:
                results["keywords"] = result.data

        if "translate" in request.tasks and request.target_languages:
            agent = TranslationAgent()
            translations = []
            for lang in request.target_languages:
                result = await agent.execute(
                    text=request.text,
                    target_language=lang,
                )
                if result.success:
                    translations.append(result.data)
            results["translations"] = translations

        return {
            "success": True,
            "original_text": request.text[:500] + "..." if len(request.text) > 500 else request.text,
            "results": results,
        }

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket endpoint for real-time updates."""
        await websocket.accept()
        active_connections[client_id] = websocket

        try:
            while True:
                data = await websocket.receive_json()
                await handle_websocket_message(websocket, client_id, data)
        except WebSocketDisconnect:
            del active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def handle_websocket_message(
        websocket: WebSocket,
        client_id: str,
        data: Dict[str, Any]
    ):
        """Handle incoming WebSocket messages."""
        message_type = data.get("type")

        if message_type == "analyze_text":
            await process_text_via_websocket(websocket, data)
        elif message_type == "process_audio":
            await process_audio_via_websocket(websocket, data)
        elif message_type == "ping":
            await websocket.send_json({"type": "pong"})

    async def process_text_via_websocket(websocket: WebSocket, data: Dict[str, Any]):
        """Process text analysis with real-time updates."""
        text = data.get("text", "")
        tasks = data.get("tasks", ["summarize", "intent", "keywords"])

        await websocket.send_json({
            "type": "status",
            "message": "Starting analysis...",
            "progress": 0,
        })

        results = {}
        total_tasks = len(tasks)
        completed = 0

        if "summarize" in tasks:
            await websocket.send_json({
                "type": "status",
                "message": "Generating summary...",
                "progress": int((completed / total_tasks) * 100),
            })
            agent = SummarizationAgent()
            result = await agent.execute(text=text, summary_type="general")
            if result.success:
                results["summary"] = result.data
            completed += 1

        if "intent" in tasks:
            await websocket.send_json({
                "type": "status",
                "message": "Detecting intent...",
                "progress": int((completed / total_tasks) * 100),
            })
            agent = IntentDetectionAgent()
            result = await agent.execute(text=text)
            if result.success:
                results["intent"] = result.data
            completed += 1

        if "keywords" in tasks:
            await websocket.send_json({
                "type": "status",
                "message": "Extracting keywords...",
                "progress": int((completed / total_tasks) * 100),
            })
            agent = KeywordExtractionAgent()
            result = await agent.execute(text=text)
            if result.success:
                results["keywords"] = result.data
            completed += 1

        await websocket.send_json({
            "type": "complete",
            "results": results,
            "progress": 100,
        })

    async def process_audio_via_websocket(websocket: WebSocket, data: Dict[str, Any]):
        """Process audio with real-time updates."""
        file_id = data.get("file_id")
        tasks = data.get("tasks", ["transcribe", "summarize", "intent", "keywords"])

        # Find file
        file_path = None
        for ext in [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".webm"]:
            potential_path = upload_dir / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break

        if not file_path:
            await websocket.send_json({
                "type": "error",
                "message": "File not found",
            })
            return

        await websocket.send_json({
            "type": "status",
            "message": "Starting audio processing...",
            "progress": 0,
        })

        # Process with orchestrator
        task_map = {
            "transcribe": ProcessingTask.TRANSCRIBE,
            "translate": ProcessingTask.TRANSLATE,
            "summarize": ProcessingTask.SUMMARIZE,
            "intent": ProcessingTask.DETECT_INTENT,
            "keywords": ProcessingTask.EXTRACT_KEYWORDS,
        }

        processing_tasks = [task_map[t] for t in tasks if t in task_map]

        try:
            orchestrator = AudioTranscriptionOrchestrator()

            # Send updates for each stage
            await websocket.send_json({
                "type": "status",
                "message": "Transcribing audio...",
                "progress": 10,
            })

            result = await orchestrator.process(
                audio_file_path=str(file_path),
                tasks=processing_tasks,
            )

            await websocket.send_json({
                "type": "complete",
                "results": format_processing_result(result),
                "progress": 100,
            })

        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })

    return app


def format_processing_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Format processing result for API response."""
    formatted = {
        "success": True,
        "duration_seconds": result.get("total_duration_seconds"),
    }

    if result.get("transcription_result"):
        tr = result["transcription_result"]
        formatted["transcription"] = {
            "text": tr.get("text"),
            "language": tr.get("language"),
            "word_count": tr.get("word_count"),
        }

    if result.get("summary_result"):
        formatted["summary"] = result["summary_result"]

    if result.get("intent_result"):
        formatted["intent"] = result["intent_result"]

    if result.get("keyword_result"):
        formatted["keywords"] = result["keyword_result"]

    if result.get("translation_results"):
        formatted["translations"] = result["translation_results"]

    if result.get("errors"):
        formatted["errors"] = result["errors"]

    return formatted


def get_html_template() -> str:
    """Return the main HTML template from the templates directory."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    else:
        # Fallback message if template not found
        return """
<!DOCTYPE html>
<html>
<head><title>AudioInsight</title></head>
<body>
    <h1>Template not found</h1>
    <p>Please ensure the template file exists at: src/ui/templates/index.html</p>
</body>
</html>
"""


# Run the app
app = create_app()


def main():
    """Run the UI server."""
    import uvicorn
    uvicorn.run(
        "src.ui.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
