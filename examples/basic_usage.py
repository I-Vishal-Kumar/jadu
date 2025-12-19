"""Basic usage examples for the Audio Transcription Tool."""

import asyncio
from pathlib import Path

from src.config import settings
from src.database.connection import init_db
from src.orchestrator import AudioTranscriptionOrchestrator, ProcessingTask
from src.agents import (
    TranscriptionAgent,
    TranslationAgent,
    SummarizationAgent,
    IntentDetectionAgent,
    KeywordExtractionAgent,
)


async def example_single_transcription():
    """Example: Transcribe a single audio file."""
    print("=" * 50)
    print("Example: Single Transcription")
    print("=" * 50)

    agent = TranscriptionAgent()
    result = await agent.execute(
        audio_file_path="path/to/your/audio.mp3",
        language="en",  # Optional: auto-detected if not provided
        include_timestamps=True,
    )

    if result.success:
        print(f"Language: {result.data['language']}")
        print(f"Word count: {result.data['word_count']}")
        print(f"Text: {result.data['text'][:200]}...")
    else:
        print(f"Error: {result.error}")


async def example_translation():
    """Example: Translate text to multiple languages."""
    print("=" * 50)
    print("Example: Translation")
    print("=" * 50)

    agent = TranslationAgent()

    text = "Hello, welcome to our audio transcription service. We help you convert speech to text."

    # Translate to Spanish
    result = await agent.execute(
        text=text,
        target_language="es",
        source_language="en",
    )

    if result.success:
        print(f"Original: {text}")
        print(f"Spanish: {result.data['translated_text']}")

    # Translate to multiple languages
    results = await agent.translate_to_multiple(
        text=text,
        target_languages=["fr", "de", "ja"],
        source_language="en",
    )

    for r in results:
        if r.success:
            print(f"{r.data['target_language']}: {r.data['translated_text']}")


async def example_summarization():
    """Example: Summarize text."""
    print("=" * 50)
    print("Example: Summarization")
    print("=" * 50)

    agent = SummarizationAgent()

    text = """
    Today we're going to discuss the quarterly sales results. Our revenue increased by 15%
    compared to last quarter, primarily driven by the new product line we launched in March.
    The marketing team did an excellent job with the social media campaign which resulted
    in a 30% increase in website traffic. However, we noticed some challenges in the
    European market where sales were flat. We need to focus on improving our presence there.
    Action items include: hire a European sales manager, increase marketing budget for EU,
    and schedule meetings with key distributors in Germany and France.
    """

    # General summary
    result = await agent.execute(text=text, summary_type="general")

    if result.success:
        print("Summary:", result.data["summary"])
        print("\nKey Points:")
        for point in result.data.get("key_points", []):
            print(f"  • {point}")
        print("\nTopics:", ", ".join(result.data.get("main_topics", [])))


async def example_intent_detection():
    """Example: Detect intent in text."""
    print("=" * 50)
    print("Example: Intent Detection")
    print("=" * 50)

    agent = IntentDetectionAgent()

    texts = [
        "I'm very unhappy with the product quality. It broke after just one week!",
        "Can you tell me more about your premium subscription plans?",
        "Great service! The team was very helpful and responsive.",
        "I need to schedule a meeting with the support team urgently.",
    ]

    for text in texts:
        result = await agent.execute(text=text)
        if result.success:
            print(f"\nText: {text[:50]}...")
            print(f"Intent: {result.data['primary_intent']}")
            print(f"Confidence: {result.data['confidence']:.1%}")
            print(f"Sentiment: {result.data['sentiment']}")
            print(f"Urgency: {result.data['urgency']}")


async def example_keyword_extraction():
    """Example: Extract keywords from text."""
    print("=" * 50)
    print("Example: Keyword Extraction")
    print("=" * 50)

    agent = KeywordExtractionAgent()

    text = """
    Machine learning and artificial intelligence are transforming the healthcare industry.
    Deep learning models can now diagnose diseases from medical images with high accuracy.
    Companies like Google Health and IBM Watson are leading this revolution.
    Neural networks analyze patient data to predict health outcomes and recommend treatments.
    """

    result = await agent.execute(text=text, max_keywords=15)

    if result.success:
        print(f"Main Theme: {result.data['main_theme']}")
        print(f"Domain: {result.data['domain']}")
        print("\nKeywords:")
        for kw in result.data["keywords"]:
            print(f"  • {kw['keyword']} ({kw['type']}, score: {kw['relevance_score']:.2f})")


async def example_full_pipeline():
    """Example: Run the full processing pipeline."""
    print("=" * 50)
    print("Example: Full Pipeline")
    print("=" * 50)

    orchestrator = AudioTranscriptionOrchestrator()

    result = await orchestrator.process(
        audio_file_path="path/to/your/audio.mp3",
        tasks=[ProcessingTask.FULL_PIPELINE],
        target_languages=["es", "fr"],  # Optional translation
    )

    print(f"Duration: {result['total_duration_seconds']:.2f}s")

    if result.get("transcription_result"):
        print(f"\nTranscription: {result['transcription_result']['text'][:200]}...")

    if result.get("summary_result"):
        print(f"\nSummary: {result['summary_result']['summary']}")

    if result.get("intent_result"):
        ir = result["intent_result"]
        print(f"\nIntent: {ir['primary_intent']} ({ir['confidence']:.0%})")

    if result.get("keyword_result"):
        keywords = [kw["keyword"] for kw in result["keyword_result"]["keywords"][:5]]
        print(f"\nTop Keywords: {', '.join(keywords)}")


async def example_selective_processing():
    """Example: Run selective tasks."""
    print("=" * 50)
    print("Example: Selective Processing")
    print("=" * 50)

    orchestrator = AudioTranscriptionOrchestrator()

    # Only transcribe and summarize
    result = await orchestrator.process(
        audio_file_path="path/to/your/audio.mp3",
        tasks=[
            ProcessingTask.TRANSCRIBE,
            ProcessingTask.SUMMARIZE,
        ],
        summary_type="key_points",
    )

    print(f"Completed tasks: {[r.task.value for r in result['task_history']]}")


async def main():
    """Run all examples."""
    # Initialize database
    settings.ensure_directories()
    await init_db()

    # Note: These examples use placeholder paths
    # Replace with actual audio file paths to test

    # Run text-based examples (no audio file needed)
    await example_translation()
    await example_summarization()
    await example_intent_detection()
    await example_keyword_extraction()

    # Uncomment to run audio examples (requires actual audio files)
    # await example_single_transcription()
    # await example_full_pipeline()
    # await example_selective_processing()


if __name__ == "__main__":
    asyncio.run(main())
