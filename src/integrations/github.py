"""GitHub integration for fetching audio files from repositories."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import httpx

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GitHubFile:
    """Represents a file from a GitHub repository."""

    name: str
    path: str
    download_url: str
    size: int
    sha: str


class GitHubIntegration:
    """Integration for fetching audio files from GitHub repositories."""

    AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma"}
    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize GitHub integration.

        Args:
            token: GitHub personal access token
            repo: Repository in format 'owner/repo'
        """
        self.token = token or settings.github_token
        self.repo = repo or settings.github_repo
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AudioTranscriptionTool/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(headers=self.headers, timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_audio_files(
        self,
        path: str = "",
        recursive: bool = True,
    ) -> List[GitHubFile]:
        """
        List audio files in the repository.

        Args:
            path: Path within the repository (default: root)
            recursive: Whether to search recursively

        Returns:
            List of GitHubFile objects for audio files
        """
        if not self.repo:
            raise ValueError("GitHub repository not configured")

        client = await self._get_client()
        audio_files = []

        async def fetch_contents(dir_path: str) -> None:
            url = f"{self.GITHUB_API_BASE}/repos/{self.repo}/contents/{dir_path}"
            response = await client.get(url)
            response.raise_for_status()

            contents = response.json()
            if not isinstance(contents, list):
                contents = [contents]

            for item in contents:
                if item["type"] == "file":
                    ext = Path(item["name"]).suffix.lower()
                    if ext in self.AUDIO_EXTENSIONS:
                        audio_files.append(GitHubFile(
                            name=item["name"],
                            path=item["path"],
                            download_url=item["download_url"],
                            size=item["size"],
                            sha=item["sha"],
                        ))
                elif item["type"] == "dir" and recursive:
                    await fetch_contents(item["path"])

        await fetch_contents(path)
        logger.info(f"Found {len(audio_files)} audio files in {self.repo}")
        return audio_files

    async def download_file(
        self,
        file: GitHubFile,
        destination: Optional[Path] = None,
    ) -> Path:
        """
        Download an audio file from GitHub.

        Args:
            file: GitHubFile object to download
            destination: Optional destination path

        Returns:
            Path to the downloaded file
        """
        if destination is None:
            destination = settings.audio_storage_path / file.name

        destination.parent.mkdir(parents=True, exist_ok=True)

        client = await self._get_client()
        response = await client.get(file.download_url)
        response.raise_for_status()

        with open(destination, "wb") as f:
            f.write(response.content)

        logger.info(f"Downloaded {file.name} to {destination}")
        return destination

    async def download_all_audio_files(
        self,
        path: str = "",
        destination_dir: Optional[Path] = None,
    ) -> List[Path]:
        """
        Download all audio files from the repository.

        Args:
            path: Path within the repository
            destination_dir: Directory to save files

        Returns:
            List of paths to downloaded files
        """
        audio_files = await self.list_audio_files(path)
        destination_dir = destination_dir or settings.audio_storage_path
        destination_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        for audio_file in audio_files:
            try:
                dest = destination_dir / audio_file.name
                await self.download_file(audio_file, dest)
                downloaded.append(dest)
            except Exception as e:
                logger.error(f"Failed to download {audio_file.name}: {e}")

        return downloaded

    async def get_file_content(self, file_path: str) -> bytes:
        """
        Get the raw content of a file from the repository.

        Args:
            file_path: Path to the file in the repository

        Returns:
            File content as bytes
        """
        if not self.repo:
            raise ValueError("GitHub repository not configured")

        client = await self._get_client()

        # Get file info
        url = f"{self.GITHUB_API_BASE}/repos/{self.repo}/contents/{file_path}"
        response = await client.get(url)
        response.raise_for_status()

        file_info = response.json()

        # Download content
        download_response = await client.get(file_info["download_url"])
        download_response.raise_for_status()

        return download_response.content

    async def create_file(
        self,
        path: str,
        content: bytes,
        message: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Create or update a file in the repository.

        Args:
            path: Path for the file in the repository
            content: File content
            message: Commit message
            branch: Branch name

        Returns:
            API response data
        """
        if not self.repo:
            raise ValueError("GitHub repository not configured")
        if not self.token:
            raise ValueError("GitHub token required for write operations")

        import base64

        client = await self._get_client()
        url = f"{self.GITHUB_API_BASE}/repos/{self.repo}/contents/{path}"

        # Check if file exists to get SHA
        sha = None
        try:
            response = await client.get(url)
            if response.status_code == 200:
                sha = response.json()["sha"]
        except Exception:
            pass

        # Create/update file
        data = {
            "message": message,
            "content": base64.b64encode(content).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            data["sha"] = sha

        response = await client.put(url, json=data)
        response.raise_for_status()

        return response.json()

    async def upload_results(
        self,
        results: Dict[str, Any],
        filename: str = "transcription_results.json",
        branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Upload processing results to the repository.

        Args:
            results: Results dictionary to upload
            filename: Name for the results file
            branch: Branch to upload to

        Returns:
            API response data
        """
        import json

        content = json.dumps(results, indent=2, ensure_ascii=False, default=str).encode("utf-8")

        return await self.create_file(
            path=f"results/{filename}",
            content=content,
            message=f"Add transcription results: {filename}",
            branch=branch,
        )

    async def __aenter__(self) -> "GitHubIntegration":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# Example usage
async def example_github_usage():
    """Example of using GitHub integration."""
    async with GitHubIntegration(repo="owner/audio-repo") as github:
        # List audio files
        files = await github.list_audio_files()
        print(f"Found {len(files)} audio files")

        # Download all files
        if files:
            downloaded = await github.download_all_audio_files()
            print(f"Downloaded {len(downloaded)} files")


if __name__ == "__main__":
    asyncio.run(example_github_usage())
