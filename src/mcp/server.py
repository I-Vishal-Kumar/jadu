"""MCP Server for database connectivity."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from src.mcp.tools import DatabaseTools
from src.database.connection import init_db

logger = logging.getLogger(__name__)


class MCPDatabaseServer:
    """MCP Server exposing database operations as tools."""

    def __init__(self):
        self.server = Server("audio-transcription-db")
        self.db_tools = DatabaseTools()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available database tools."""
            return [
                # Audio File Tools
                Tool(
                    name="create_audio_file",
                    description="Create a new audio file record in the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name of the audio file"},
                            "file_path": {"type": "string", "description": "Full path to the audio file"},
                            "file_size_bytes": {"type": "integer", "description": "File size in bytes"},
                            "duration_seconds": {"type": "number", "description": "Audio duration in seconds"},
                            "format": {"type": "string", "description": "Audio format (mp3, wav, etc.)"},
                            "sample_rate": {"type": "integer", "description": "Sample rate in Hz"},
                            "channels": {"type": "integer", "description": "Number of audio channels"},
                            "extra_data": {"type": "object", "description": "Additional data"},
                        },
                        "required": ["filename", "file_path"],
                    },
                ),
                Tool(
                    name="get_audio_file",
                    description="Get an audio file record by ID with all related data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_file_id": {"type": "integer", "description": "Audio file ID"},
                        },
                        "required": ["audio_file_id"],
                    },
                ),
                Tool(
                    name="list_audio_files",
                    description="List audio files with optional status filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]},
                            "limit": {"type": "integer", "default": 100},
                            "offset": {"type": "integer", "default": 0},
                        },
                    },
                ),
                Tool(
                    name="update_audio_file_status",
                    description="Update the processing status of an audio file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_file_id": {"type": "integer", "description": "Audio file ID"},
                            "status": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]},
                        },
                        "required": ["audio_file_id", "status"],
                    },
                ),
                Tool(
                    name="delete_audio_file",
                    description="Delete an audio file and all related data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_file_id": {"type": "integer", "description": "Audio file ID"},
                        },
                        "required": ["audio_file_id"],
                    },
                ),
                # Transcript Tools
                Tool(
                    name="create_transcript",
                    description="Create a new transcript for an audio file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_file_id": {"type": "integer", "description": "Audio file ID"},
                            "text": {"type": "string", "description": "Transcribed text"},
                            "language": {"type": "string", "default": "en"},
                            "confidence": {"type": "number", "description": "Transcription confidence score"},
                            "word_timestamps": {"type": "object", "description": "Word-level timestamps"},
                            "model_used": {"type": "string", "description": "Model used for transcription"},
                        },
                        "required": ["audio_file_id", "text"],
                    },
                ),
                Tool(
                    name="get_transcript",
                    description="Get a transcript by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                        },
                        "required": ["transcript_id"],
                    },
                ),
                Tool(
                    name="get_transcript_by_audio_file",
                    description="Get transcript by audio file ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_file_id": {"type": "integer", "description": "Audio file ID"},
                        },
                        "required": ["audio_file_id"],
                    },
                ),
                # Translation Tools
                Tool(
                    name="create_translation",
                    description="Create a new translation for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                            "target_language": {"type": "string", "description": "Target language code"},
                            "translated_text": {"type": "string", "description": "Translated text"},
                            "model_used": {"type": "string", "description": "Model used for translation"},
                        },
                        "required": ["transcript_id", "target_language", "translated_text"],
                    },
                ),
                Tool(
                    name="get_translations",
                    description="Get all translations for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                        },
                        "required": ["transcript_id"],
                    },
                ),
                # Summary Tools
                Tool(
                    name="create_summary",
                    description="Create a new summary for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                            "summary_text": {"type": "string", "description": "Summary text"},
                            "summary_type": {"type": "string", "default": "general", "enum": ["general", "key_points", "action_items"]},
                            "key_points": {"type": "array", "items": {"type": "string"}},
                            "model_used": {"type": "string", "description": "Model used for summarization"},
                        },
                        "required": ["transcript_id", "summary_text"],
                    },
                ),
                Tool(
                    name="get_summaries",
                    description="Get all summaries for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                        },
                        "required": ["transcript_id"],
                    },
                ),
                # Intent Tools
                Tool(
                    name="create_intent",
                    description="Create a new intent classification for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                            "category": {"type": "string", "enum": ["inquiry", "complaint", "feedback", "request", "information", "support", "sales", "other"]},
                            "confidence": {"type": "number", "description": "Classification confidence score"},
                            "reasoning": {"type": "string", "description": "Reasoning for the classification"},
                            "sub_intents": {"type": "array", "items": {"type": "string"}},
                            "model_used": {"type": "string", "description": "Model used for classification"},
                        },
                        "required": ["transcript_id", "category", "confidence"],
                    },
                ),
                Tool(
                    name="get_intents",
                    description="Get all intent classifications for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                        },
                        "required": ["transcript_id"],
                    },
                ),
                # Keyword Tools
                Tool(
                    name="create_keywords",
                    description="Create multiple keywords for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                            "keywords": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "keyword": {"type": "string"},
                                        "type": {"type": "string", "enum": ["keyword", "keyphrase", "entity"]},
                                        "relevance_score": {"type": "number"},
                                        "frequency": {"type": "integer"},
                                        "context": {"type": "string"},
                                    },
                                    "required": ["keyword"],
                                },
                            },
                        },
                        "required": ["transcript_id", "keywords"],
                    },
                ),
                Tool(
                    name="get_keywords",
                    description="Get all keywords for a transcript",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "transcript_id": {"type": "integer", "description": "Transcript ID"},
                        },
                        "required": ["transcript_id"],
                    },
                ),
                # Search Tools
                Tool(
                    name="search_transcripts",
                    description="Search transcripts containing the query text",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "default": 20},
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="get_transcripts_by_intent",
                    description="Get transcripts by intent category",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": ["inquiry", "complaint", "feedback", "request", "information", "support", "sales", "other"]},
                            "min_confidence": {"type": "number", "default": 0.5},
                        },
                        "required": ["category"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                # Map tool names to methods
                tool_methods: Dict[str, Callable] = {
                    "create_audio_file": self.db_tools.create_audio_file,
                    "get_audio_file": self.db_tools.get_audio_file,
                    "list_audio_files": self.db_tools.list_audio_files,
                    "update_audio_file_status": self.db_tools.update_audio_file_status,
                    "delete_audio_file": self.db_tools.delete_audio_file,
                    "create_transcript": self.db_tools.create_transcript,
                    "get_transcript": self.db_tools.get_transcript,
                    "get_transcript_by_audio_file": self.db_tools.get_transcript_by_audio_file,
                    "create_translation": self.db_tools.create_translation,
                    "get_translations": self.db_tools.get_translations,
                    "create_summary": self.db_tools.create_summary,
                    "get_summaries": self.db_tools.get_summaries,
                    "create_intent": self.db_tools.create_intent,
                    "get_intents": self.db_tools.get_intents,
                    "create_keywords": self.db_tools.create_keywords,
                    "get_keywords": self.db_tools.get_keywords,
                    "search_transcripts": self.db_tools.search_transcripts,
                    "get_transcripts_by_intent": self.db_tools.get_transcripts_by_intent,
                }

                if name not in tool_methods:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True,
                    )

                result = await tool_methods[name](**arguments)
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2))],
                    isError=False,
                )

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True,
                )

    async def run(self) -> None:
        """Run the MCP server."""
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


def main():
    """Main entry point for the MCP server."""
    logging.basicConfig(level=logging.INFO)
    server = MCPDatabaseServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
