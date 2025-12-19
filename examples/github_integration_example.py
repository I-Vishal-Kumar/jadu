"""Example of using GitHub integration to process audio files from a repository."""

import asyncio
import json
from pathlib import Path

from src.config import settings
from src.database.connection import init_db
from src.integrations.github import GitHubIntegration
from src.orchestrator import AudioTranscriptionOrchestrator, ProcessingTask


async def process_repo_audio_files():
    """
    Download and process all audio files from a GitHub repository.

    This example demonstrates:
    1. Connecting to a GitHub repository
    2. Listing all audio files
    3. Downloading audio files
    4. Processing each file through the full pipeline
    5. Uploading results back to the repository
    """
    print("=" * 60)
    print("GitHub Audio Processing Pipeline")
    print("=" * 60)

    # Initialize database
    settings.ensure_directories()
    await init_db()

    # Configure GitHub (set these in .env or pass directly)
    github_token = settings.github_token
    github_repo = settings.github_repo  # e.g., "owner/audio-files-repo"

    if not github_repo:
        print("Error: GitHub repository not configured. Set GITHUB_REPO in .env")
        return

    async with GitHubIntegration(token=github_token, repo=github_repo) as github:
        # List audio files in the repository
        print("\n📁 Listing audio files in repository...")
        audio_files = await github.list_audio_files(path="audio", recursive=True)

        if not audio_files:
            print("No audio files found in repository.")
            return

        print(f"Found {len(audio_files)} audio files:")
        for f in audio_files:
            print(f"  • {f.name} ({f.size / 1024:.1f} KB)")

        # Download files
        print("\n📥 Downloading audio files...")
        downloaded_files = await github.download_all_audio_files(path="audio")
        print(f"Downloaded {len(downloaded_files)} files")

        # Process each file
        orchestrator = AudioTranscriptionOrchestrator()
        all_results = []

        for audio_path in downloaded_files:
            print(f"\n🔄 Processing: {audio_path.name}")

            try:
                result = await orchestrator.process_full_pipeline(
                    audio_file_path=str(audio_path),
                    target_languages=["es"],  # Optional: translate to Spanish
                )

                # Summarize result
                summary = {
                    "file": audio_path.name,
                    "status": "success",
                    "duration_seconds": result.get("total_duration_seconds"),
                    "transcript_preview": result.get("transcription_result", {}).get("text", "")[:200],
                    "intent": result.get("intent_result", {}).get("primary_intent"),
                    "sentiment": result.get("intent_result", {}).get("sentiment"),
                    "keywords": [
                        kw["keyword"]
                        for kw in result.get("keyword_result", {}).get("keywords", [])[:5]
                    ],
                }

                if result.get("summary_result"):
                    summary["summary"] = result["summary_result"]["summary"]

                all_results.append(summary)

                print(f"  ✅ Completed in {summary['duration_seconds']:.2f}s")
                print(f"  Intent: {summary.get('intent', 'N/A')}")
                print(f"  Keywords: {', '.join(summary.get('keywords', []))}")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                all_results.append({
                    "file": audio_path.name,
                    "status": "error",
                    "error": str(e),
                })

        # Upload results to repository
        print("\n📤 Uploading results to repository...")
        try:
            await github.upload_results(
                results={
                    "processed_files": len(all_results),
                    "successful": len([r for r in all_results if r["status"] == "success"]),
                    "results": all_results,
                },
                filename="audio_processing_results.json",
            )
            print("Results uploaded successfully!")
        except Exception as e:
            print(f"Failed to upload results: {e}")

            # Save locally instead
            output_path = Path("results") / "audio_processing_results.json"
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(all_results, f, indent=2)
            print(f"Results saved locally to: {output_path}")

    print("\n✅ Processing complete!")


async def main():
    """Run the GitHub integration example."""
    await process_repo_audio_files()


if __name__ == "__main__":
    asyncio.run(main())
