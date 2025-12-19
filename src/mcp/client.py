"""MCP Client for connecting to MCP servers."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for connecting to MCP servers and invoking tools."""

    def __init__(self, server_command: str, server_args: Optional[List[str]] = None):
        """
        Initialize MCP client.

        Args:
            server_command: Command to start the MCP server
            server_args: Optional arguments for the server command
        """
        self.server_params = StdioServerParameters(
            command=server_command,
            args=server_args or [],
        )
        self.session: Optional[ClientSession] = None
        self._read = None
        self._write = None

    async def connect(self) -> None:
        """Connect to the MCP server."""
        self._read, self._write = await stdio_client(self.server_params).__aenter__()
        self.session = ClientSession(self._read, self._write)
        await self.session.__aenter__()
        await self.session.initialize()
        logger.info("Connected to MCP server")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        logger.info("Disconnected from MCP server")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        result = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in result.tools
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            name: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            Tool result as a dictionary
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        result = await self.session.call_tool(name, arguments)

        # Parse the result content
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, "text"):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return {"text": content.text}
            return {"content": str(content)}

        return {"result": "empty"}

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()


class DatabaseMCPClient(MCPClient):
    """Specialized MCP client for database operations."""

    def __init__(self):
        """Initialize the database MCP client."""
        super().__init__(
            server_command="python",
            server_args=["-m", "src.mcp.server"],
        )

    # Audio File Operations
    async def create_audio_file(
        self,
        filename: str,
        file_path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a new audio file record."""
        return await self.call_tool("create_audio_file", {
            "filename": filename,
            "file_path": file_path,
            **kwargs,
        })

    async def get_audio_file(self, audio_file_id: int) -> Dict[str, Any]:
        """Get an audio file by ID."""
        return await self.call_tool("get_audio_file", {"audio_file_id": audio_file_id})

    async def list_audio_files(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List audio files."""
        args = {"limit": limit, "offset": offset}
        if status:
            args["status"] = status
        return await self.call_tool("list_audio_files", args)

    async def update_audio_file_status(
        self, audio_file_id: int, status: str
    ) -> Dict[str, Any]:
        """Update audio file status."""
        return await self.call_tool("update_audio_file_status", {
            "audio_file_id": audio_file_id,
            "status": status,
        })

    # Transcript Operations
    async def create_transcript(
        self,
        audio_file_id: int,
        text: str,
        language: str = "en",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a transcript."""
        return await self.call_tool("create_transcript", {
            "audio_file_id": audio_file_id,
            "text": text,
            "language": language,
            **kwargs,
        })

    async def get_transcript(self, transcript_id: int) -> Dict[str, Any]:
        """Get a transcript by ID."""
        return await self.call_tool("get_transcript", {"transcript_id": transcript_id})

    async def search_transcripts(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search transcripts."""
        return await self.call_tool("search_transcripts", {"query": query, "limit": limit})

    # Summary Operations
    async def create_summary(
        self,
        transcript_id: int,
        summary_text: str,
        summary_type: str = "general",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a summary."""
        return await self.call_tool("create_summary", {
            "transcript_id": transcript_id,
            "summary_text": summary_text,
            "summary_type": summary_type,
            **kwargs,
        })

    # Intent Operations
    async def create_intent(
        self,
        transcript_id: int,
        category: str,
        confidence: float,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create an intent classification."""
        return await self.call_tool("create_intent", {
            "transcript_id": transcript_id,
            "category": category,
            "confidence": confidence,
            **kwargs,
        })

    async def get_transcripts_by_intent(
        self, category: str, min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Get transcripts by intent category."""
        return await self.call_tool("get_transcripts_by_intent", {
            "category": category,
            "min_confidence": min_confidence,
        })


# Example usage
async def example_usage():
    """Example of using the MCP client."""
    async with DatabaseMCPClient() as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t['name'] for t in tools]}")

        # Create an audio file record
        audio = await client.create_audio_file(
            filename="test.mp3",
            file_path="/path/to/test.mp3",
            duration_seconds=120.5,
        )
        print(f"Created audio file: {audio}")

        # List audio files
        files = await client.list_audio_files(limit=10)
        print(f"Audio files: {files}")


if __name__ == "__main__":
    asyncio.run(example_usage())
