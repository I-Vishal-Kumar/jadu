# Audio Transcription and Intent Summary Tool

A powerful audio processing tool built with LangChain that provides transcription, translation, summarization, intent detection, and keyword extraction capabilities. Features an orchestrator pattern with specialized agents and MCP (Model Context Protocol) for database connectivity.

## Features

- **Audio Transcription**: Convert audio files to text using OpenAI Whisper
- **Translation**: Translate transcripts to 30+ languages
- **Summarization**: Generate summaries with key points and action items
- **Intent Detection**: Classify content into categories (inquiry, complaint, feedback, etc.)
- **Keyword Extraction**: Extract keywords, keyphrases, and named entities
- **Multi-Provider Support**: Works with OpenAI and Anthropic Claude
- **MCP Database Integration**: Store and query results through MCP protocol
- **GitHub Integration**: Process audio files from GitHub repositories
- **Modern Web UI**: Perplexity-style interface with real-time updates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│                    (LangGraph Workflow)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │Transcribe│ │Translate │ │Summarize │ │  Intent  │        │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
│       │            │            │            │               │
│  ┌────┴─────┐                                                │
│  │ Keyword  │                                                │
│  │  Agent   │                                                │
│  └────┬─────┘                                                │
│       │                                                      │
├───────┴──────────────────────────────────────────────────────┤
│                    MCP Database Server                       │
│                      (SQLite/Tools)                          │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start (One-Click Setup)

### Windows - Easiest Method

Just double-click one of these files:

```
setup_and_run.bat      # For Command Prompt
setup_and_run.ps1      # For PowerShell
```

This will automatically:
1. Create a virtual environment
2. Install all dependencies
3. Prompt you to add API keys
4. Start the web server

Then open **http://localhost:8000** in your browser.

---

## Manual Installation

### Prerequisites

- Python 3.10+
- FFmpeg (for audio processing)

### Option 1: With Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install with UI dependencies
pip install -e ".[ui]"

# Copy and edit environment file
copy .env.example .env
# Edit .env with your API keys

# Run the UI
python run_ui.py
```

### Option 2: Global Installation

```bash
pip install -e ".[ui]"
```

### Environment Variables

Create a `.env` file with your API keys:

```env
# Required: At least one LLM provider
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Default provider
DEFAULT_LLM_PROVIDER=openai  # or anthropic

# Optional: GitHub integration
GITHUB_TOKEN=your-github-token
GITHUB_REPO=owner/repo-name
```

## Usage

### Web UI (Recommended)

Start the server and open http://localhost:8000:

```bash
python run_ui.py
```

**Features:**
- Drag & drop audio file upload
- Real-time processing updates via WebSocket
- Chat-style interface for text analysis
- Toggle analysis options (Summary, Intent, Keywords, Translation)
- Beautiful Perplexity-inspired dark theme

![UI Screenshot](docs/ui-screenshot.png)

### Command Line Interface

```bash
# Transcribe an audio file
python -m src.main transcribe audio.mp3

# Transcribe with timestamps
python -m src.main transcribe audio.mp3 --timestamps

# Full pipeline processing
python -m src.main full-pipeline audio.mp3

# Full pipeline with translation
python -m src.main full-pipeline audio.mp3 --translate es fr de

# Selective processing
python -m src.main process audio.mp3 --summarize --intent --keywords

# Use specific provider
python -m src.main transcribe audio.mp3 --provider anthropic

# Save results to file
python -m src.main full-pipeline audio.mp3 --output results.json
```

### Python API

```python
import asyncio
from src.orchestrator import AudioTranscriptionOrchestrator, ProcessingTask

async def process_audio():
    orchestrator = AudioTranscriptionOrchestrator()

    result = await orchestrator.process(
        audio_file_path="audio.mp3",
        tasks=[ProcessingTask.FULL_PIPELINE],
        target_languages=["es", "fr"],
    )

    print(f"Transcript: {result['transcription_result']['text']}")
    print(f"Summary: {result['summary_result']['summary']}")
    print(f"Intent: {result['intent_result']['primary_intent']}")

asyncio.run(process_audio())
```

### Individual Agents

```python
from src.agents import (
    TranscriptionAgent,
    TranslationAgent,
    SummarizationAgent,
    IntentDetectionAgent,
    KeywordExtractionAgent,
)

# Transcription
agent = TranscriptionAgent()
result = await agent.execute(audio_file_path="audio.mp3")

# Translation
agent = TranslationAgent()
result = await agent.execute(
    text="Hello world",
    target_language="es",
)

# Summarization
agent = SummarizationAgent()
result = await agent.execute(
    text="Long text to summarize...",
    summary_type="key_points",
)

# Intent Detection
agent = IntentDetectionAgent()
result = await agent.execute(text="I need help with my order")

# Keyword Extraction
agent = KeywordExtractionAgent()
result = await agent.execute(text="Text with keywords...")
```

### LangChain Integration

```python
from src.tools import get_all_tools
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI

# Get all audio processing tools
tools = get_all_tools()

# Create an agent with these tools
llm = ChatOpenAI(model="gpt-4o")
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# Use the agent
response = await executor.ainvoke({
    "input": "Transcribe and summarize audio.mp3"
})
```

### MCP Server

Run the MCP server for database connectivity:

```bash
python -m src.mcp.server
```

MCP tools available:
- `create_audio_file` / `get_audio_file` / `list_audio_files`
- `create_transcript` / `get_transcript` / `search_transcripts`
- `create_translation` / `get_translations`
- `create_summary` / `get_summaries`
- `create_intent` / `get_intents`
- `create_keywords` / `get_keywords`
- `get_transcripts_by_intent`

### GitHub Integration

```python
from src.integrations.github import GitHubIntegration

async with GitHubIntegration(repo="owner/repo") as github:
    # List audio files
    files = await github.list_audio_files()

    # Download all audio files
    downloaded = await github.download_all_audio_files()

    # Upload results
    await github.upload_results(results, filename="results.json")
```

## Project Structure

```
audio-transcription/
├── src/
│   ├── agents/              # Specialized processing agents
│   │   ├── base.py          # Base agent class
│   │   ├── transcription.py # Whisper transcription
│   │   ├── translation.py   # Language translation
│   │   ├── summarization.py # Text summarization
│   │   ├── intent.py        # Intent detection
│   │   └── keyword.py       # Keyword extraction
│   ├── database/            # Database models and connection
│   │   ├── models.py        # SQLAlchemy models
│   │   └── connection.py    # Database manager
│   ├── integrations/        # External integrations
│   │   └── github.py        # GitHub repository integration
│   ├── llm/                 # LLM provider management
│   │   └── provider.py      # Multi-provider factory
│   ├── mcp/                 # MCP server and client
│   │   ├── server.py        # MCP database server
│   │   ├── client.py        # MCP client
│   │   └── tools.py         # Database tools
│   ├── orchestrator/        # Workflow orchestration
│   │   ├── state.py         # Workflow state definitions
│   │   └── workflow.py      # LangGraph workflow
│   ├── tools/               # LangChain tool wrappers
│   │   └── langchain_tools.py
│   ├── ui/                  # Web UI
│   │   └── app.py           # FastAPI application
│   ├── config.py            # Configuration management
│   └── main.py              # CLI entry point
├── run_ui.py                # UI server launcher
├── examples/                # Usage examples
├── data/                    # Data storage (created at runtime)
│   ├── audio/               # Downloaded audio files
│   └── transcriptions.db    # SQLite database
├── pyproject.toml           # Project dependencies
└── .env.example             # Environment template
```

## Supported Audio Formats

- MP3, WAV, FLAC, M4A, OGG, AAC, WMA

## Supported Languages

Translation supports 30+ languages including:
- English, Spanish, French, German, Italian, Portuguese
- Chinese, Japanese, Korean, Arabic, Hindi
- Russian, Turkish, Dutch, Polish, and more

## Intent Categories

- **Inquiry**: Questions seeking information
- **Complaint**: Expressions of dissatisfaction
- **Feedback**: General feedback and suggestions
- **Request**: Requests for action or service
- **Information**: Sharing information
- **Support**: Technical support requests
- **Sales**: Sales-related discussions
- **Other**: Uncategorized content

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Code Formatting

```bash
black src/
ruff check src/ --fix
```

## License

MIT License
