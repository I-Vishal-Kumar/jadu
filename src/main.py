"""Main entry point for the Audio Transcription Tool."""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from src.config import settings
from src.database.connection import init_db
from src.orchestrator import AudioTranscriptionOrchestrator, ProcessingTask


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Audio Transcription and Intent Summary Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe a single audio file
  python -m src.main transcribe audio.mp3

  # Full pipeline with translation
  python -m src.main full-pipeline audio.mp3 --translate es fr de

  # Summarize and detect intent
  python -m src.main process audio.mp3 --summarize --intent

  # Extract keywords only
  python -m src.main process audio.mp3 --keywords --max-keywords 30
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Transcribe command
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe audio file")
    transcribe_parser.add_argument("audio_file", type=str, help="Path to audio file")
    transcribe_parser.add_argument(
        "--language", "-l", type=str, default=None, help="Source language code"
    )
    transcribe_parser.add_argument(
        "--timestamps", "-t", action="store_true", help="Include word timestamps"
    )

    # Process command (selective tasks)
    process_parser = subparsers.add_parser("process", help="Process audio with selected tasks")
    process_parser.add_argument("audio_file", type=str, help="Path to audio file")
    process_parser.add_argument(
        "--transcribe", action="store_true", help="Transcribe audio"
    )
    process_parser.add_argument(
        "--translate", "-T", nargs="+", metavar="LANG", help="Translate to languages"
    )
    process_parser.add_argument(
        "--summarize", "-s", action="store_true", help="Generate summary"
    )
    process_parser.add_argument(
        "--summary-type", choices=["general", "key_points", "action_items", "quick"],
        default="general", help="Type of summary"
    )
    process_parser.add_argument(
        "--intent", "-i", action="store_true", help="Detect intent"
    )
    process_parser.add_argument(
        "--keywords", "-k", action="store_true", help="Extract keywords"
    )
    process_parser.add_argument(
        "--max-keywords", type=int, default=20, help="Maximum keywords to extract"
    )
    process_parser.add_argument(
        "--language", "-l", type=str, default="en", help="Source language code"
    )

    # Full pipeline command
    full_parser = subparsers.add_parser("full-pipeline", help="Run full processing pipeline")
    full_parser.add_argument("audio_file", type=str, help="Path to audio file")
    full_parser.add_argument(
        "--translate", "-T", nargs="*", metavar="LANG", help="Translate to languages"
    )
    full_parser.add_argument(
        "--language", "-l", type=str, default="en", help="Source language code"
    )

    # Common arguments
    for p in [transcribe_parser, process_parser, full_parser]:
        p.add_argument(
            "--provider", "-p", choices=["openai", "anthropic"],
            help="LLM provider to use"
        )
        p.add_argument(
            "--output", "-o", type=str, help="Output file for results (JSON)"
        )
        p.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )

    # Initialize database command
    init_parser = subparsers.add_parser("init-db", help="Initialize the database")

    return parser.parse_args()


async def run_transcribe(
    audio_file: str,
    language: Optional[str] = None,
    timestamps: bool = False,
    provider: Optional[str] = None,
) -> dict:
    """Run transcription only."""
    orchestrator = AudioTranscriptionOrchestrator(provider=provider)
    return await orchestrator.process(
        audio_file_path=audio_file,
        tasks=[ProcessingTask.TRANSCRIBE],
        source_language=language or "en",
        include_timestamps=timestamps,
    )


async def run_process(
    audio_file: str,
    transcribe: bool = True,
    translate_languages: Optional[List[str]] = None,
    summarize: bool = False,
    summary_type: str = "general",
    intent: bool = False,
    keywords: bool = False,
    max_keywords: int = 20,
    language: str = "en",
    provider: Optional[str] = None,
) -> dict:
    """Run selective processing tasks."""
    tasks = []

    if transcribe:
        tasks.append(ProcessingTask.TRANSCRIBE)
    if translate_languages:
        tasks.append(ProcessingTask.TRANSLATE)
    if summarize:
        tasks.append(ProcessingTask.SUMMARIZE)
    if intent:
        tasks.append(ProcessingTask.DETECT_INTENT)
    if keywords:
        tasks.append(ProcessingTask.EXTRACT_KEYWORDS)

    if not tasks:
        # Default to transcribe if no tasks specified
        tasks.append(ProcessingTask.TRANSCRIBE)

    orchestrator = AudioTranscriptionOrchestrator(provider=provider)
    return await orchestrator.process(
        audio_file_path=audio_file,
        tasks=tasks,
        source_language=language,
        target_languages=translate_languages or [],
        summary_type=summary_type,
        max_keywords=max_keywords,
    )


async def run_full_pipeline(
    audio_file: str,
    translate_languages: Optional[List[str]] = None,
    language: str = "en",
    provider: Optional[str] = None,
) -> dict:
    """Run the full processing pipeline."""
    orchestrator = AudioTranscriptionOrchestrator(provider=provider)
    return await orchestrator.process_full_pipeline(
        audio_file_path=audio_file,
        target_languages=translate_languages or [],
    )


def format_result(result: dict) -> str:
    """Format the result for display."""
    output = []
    output.append("=" * 60)
    output.append("AUDIO TRANSCRIPTION RESULTS")
    output.append("=" * 60)

    # Transcription
    if result.get("transcription_result"):
        output.append("\n📝 TRANSCRIPTION:")
        output.append("-" * 40)
        tr = result["transcription_result"]
        output.append(f"Language: {tr.get('language', 'unknown')}")
        output.append(f"Word count: {tr.get('word_count', 0)}")
        output.append(f"\nText:\n{tr.get('text', '')[:500]}...")

    # Summary
    if result.get("summary_result"):
        output.append("\n📋 SUMMARY:")
        output.append("-" * 40)
        sr = result["summary_result"]
        output.append(sr.get("summary", ""))
        if sr.get("key_points"):
            output.append("\nKey Points:")
            for point in sr["key_points"]:
                output.append(f"  • {point}")

    # Intent
    if result.get("intent_result"):
        output.append("\n🎯 INTENT:")
        output.append("-" * 40)
        ir = result["intent_result"]
        output.append(f"Category: {ir.get('primary_intent', 'unknown')}")
        output.append(f"Confidence: {ir.get('confidence', 0):.1%}")
        output.append(f"Sentiment: {ir.get('sentiment', 'neutral')}")
        output.append(f"Urgency: {ir.get('urgency', 'medium')}")
        if ir.get("reasoning"):
            output.append(f"Reasoning: {ir['reasoning']}")

    # Keywords
    if result.get("keyword_result"):
        output.append("\n🔑 KEYWORDS:")
        output.append("-" * 40)
        kr = result["keyword_result"]
        output.append(f"Main theme: {kr.get('main_theme', 'unknown')}")
        output.append(f"Domain: {kr.get('domain', 'unknown')}")
        output.append("\nTop keywords:")
        for kw in kr.get("keywords", [])[:10]:
            output.append(f"  • {kw['keyword']} ({kw['type']}, score: {kw['relevance_score']:.2f})")

    # Translations
    if result.get("translation_results"):
        output.append("\n🌍 TRANSLATIONS:")
        output.append("-" * 40)
        for tr in result["translation_results"]:
            output.append(f"\n[{tr.get('target_language', '?')}]:")
            output.append(tr.get("translated_text", "")[:300] + "...")

    # Errors
    if result.get("errors"):
        output.append("\n⚠️ ERRORS:")
        output.append("-" * 40)
        for error in result["errors"]:
            output.append(f"  • {error}")

    # Metrics
    output.append("\n📊 METRICS:")
    output.append("-" * 40)
    output.append(f"Total duration: {result.get('total_duration_seconds', 0):.2f}s")

    completed = [h.task.value for h in result.get("task_history", []) if h.status.value == "completed"]
    output.append(f"Completed tasks: {', '.join(completed)}")

    return "\n".join(output)


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    if not args.command:
        print("Please specify a command. Use --help for usage information.")
        sys.exit(1)

    # Setup logging
    log_level = "DEBUG" if getattr(args, "verbose", False) else settings.log_level
    setup_logging(log_level)

    # Ensure directories exist
    settings.ensure_directories()

    # Initialize database
    await init_db()

    result = None

    if args.command == "init-db":
        print("Database initialized successfully!")
        return

    elif args.command == "transcribe":
        # Validate file exists
        if not Path(args.audio_file).exists():
            print(f"Error: Audio file not found: {args.audio_file}")
            sys.exit(1)

        result = await run_transcribe(
            audio_file=args.audio_file,
            language=args.language,
            timestamps=args.timestamps,
            provider=args.provider,
        )

    elif args.command == "process":
        if not Path(args.audio_file).exists():
            print(f"Error: Audio file not found: {args.audio_file}")
            sys.exit(1)

        result = await run_process(
            audio_file=args.audio_file,
            transcribe=args.transcribe or not any([
                args.summarize, args.intent, args.keywords, args.translate
            ]),
            translate_languages=args.translate,
            summarize=args.summarize,
            summary_type=args.summary_type,
            intent=args.intent,
            keywords=args.keywords,
            max_keywords=args.max_keywords,
            language=args.language,
            provider=args.provider,
        )

    elif args.command == "full-pipeline":
        if not Path(args.audio_file).exists():
            print(f"Error: Audio file not found: {args.audio_file}")
            sys.exit(1)

        result = await run_full_pipeline(
            audio_file=args.audio_file,
            translate_languages=args.translate,
            language=args.language,
            provider=args.provider,
        )

    # Output results
    if result:
        # Convert TaskResult objects to dicts for JSON serialization
        if "task_history" in result:
            result["task_history"] = [
                {
                    "task": tr.task.value,
                    "status": tr.status.value,
                    "data": tr.data,
                    "error": tr.error,
                    "duration_seconds": tr.duration_seconds,
                }
                for tr in result["task_history"]
            ]

        if hasattr(args, "output") and args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            print(f"Results saved to: {args.output}")
        else:
            print(format_result(result))


if __name__ == "__main__":
    asyncio.run(main())
