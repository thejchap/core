"""Tryke fixtures for frontend tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture


@fixture
def mock_github_api() -> Generator[AsyncMock]:
    """Mock aiogithubapi GitHubAPI."""
    with patch(
        "homeassistant.components.frontend.pr_download.GitHubAPI"
    ) as mock_gh_class:
        mock_client = AsyncMock()
        mock_gh_class.return_value = mock_client

        pr_response = AsyncMock()
        pr_response.data = {
            "head": {"sha": "abc123def456"},
            "base": {"sha": "base789abc012"},
        }

        workflow_response = AsyncMock()
        workflow_response.data = {
            "workflow_runs": [
                {
                    "id": 12345,
                    "status": "completed",
                    "conclusion": "success",
                }
            ]
        }

        artifacts_response = AsyncMock()
        artifacts_response.data = {
            "artifacts": [
                {
                    "name": "frontend-build",
                    "archive_download_url": "https://api.github.com/artifact/download",
                }
            ]
        }

        async def generic_side_effect(endpoint, **kwargs):
            if "pulls" in endpoint:
                return pr_response
            if "workflows" in endpoint and "runs" in endpoint:
                return workflow_response
            if "artifacts" in endpoint:
                return artifacts_response
            raise ValueError(f"Unexpected endpoint: {endpoint}")

        mock_client.generic.side_effect = generic_side_effect

        yield mock_client


@fixture
def mock_zipfile() -> Generator[MagicMock]:
    """Mock zipfile extraction."""
    with patch("zipfile.ZipFile") as mock_zip:
        mock_zip_instance = MagicMock()
        mock_info = MagicMock()
        mock_info.file_size = 1000
        mock_zip_instance.infolist.return_value = [mock_info]
        mock_zip.return_value.__enter__.return_value = mock_zip_instance
        yield mock_zip_instance
