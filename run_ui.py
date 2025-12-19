"""Run the Audio Transcription UI server."""

import uvicorn
from src.config import settings


def main():
    """Start the UI server."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     🎙️  Audio Transcription & Intent Summary Tool  🎙️    ║
    ║                                                           ║
    ║  Starting server at: http://localhost:8000                ║
    ║                                                           ║
    ║  Press Ctrl+C to stop the server                          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Ensure directories exist
    settings.ensure_directories()

    uvicorn.run(
        "src.ui.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
