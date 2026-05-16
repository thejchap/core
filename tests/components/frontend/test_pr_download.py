"""Tests for frontend PR download functionality."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from aiogithubapi import (
    GitHubAuthenticationException,
    GitHubException,
    GitHubNotFoundException,
    GitHubPermissionException,
    GitHubRatelimitException,
)
from aiohttp import ClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.frontend import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import mock_github_api, mock_zipfile

from tests.hass_fixtures import (
    LogCapture,
    aioclient_mock as aioclient_mock_fixture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    tmp_path as tmp_path_fixture,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor() -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test
async def pr_download_success(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    mock_zipfile: MagicMock = Depends(mock_zipfile),
) -> None:
    """Test successful PR artifact download."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    config = {
        DOMAIN: {
            "development_pr": 12345,
            "github_token": "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect(mock_github_api.generic.call_count >= 2).to_be(True)
    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    mock_zipfile.extractall.assert_called_once()


@test
async def pr_download_uses_cache(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that cached PR is used when commit hasn't changed."""
    hass.config.config_dir = str(tmp_path)

    pr_cache_dir = tmp_path / ".cache" / "frontend" / "development_artifacts"
    frontend_dir = pr_cache_dir / "hass_frontend"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "index.html").write_text("test")
    (pr_cache_dir / ".sha").write_text("abc123def456:base789abc012")

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
        mock_client.generic.return_value = pr_response

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("Using cached PR #12345" in caplog.text).to_be(True)

        calls = list(mock_client.generic.call_args_list)
        expect(len(calls)).to_equal(1)
        expect("pulls" in str(calls[0])).to_be(True)


@test.cases(
    test.case("head_changed", cache_key="old_head_sha:base789abc012"),
    test.case("base_changed", cache_key="abc123def456:old_base_sha"),
)
async def pr_download_cache_invalidated(
    cache_key: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    mock_zipfile: MagicMock = Depends(mock_zipfile),
) -> None:
    """Test that cache is invalidated when head commit changes."""
    hass.config.config_dir = str(tmp_path)

    pr_cache_dir = tmp_path / ".cache" / "frontend" / "development_artifacts"
    frontend_dir = pr_cache_dir / "hass_frontend"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "index.html").write_text("test")
    (pr_cache_dir / ".sha").write_text(cache_key)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    config = {
        DOMAIN: {
            "development_pr": 12345,
            "github_token": "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect(len(aioclient_mock.mock_calls)).to_equal(1)


@test.skip("chmod 0o000 has no effect when test process runs as root")
async def pr_download_cache_sha_read_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    mock_zipfile: MagicMock = Depends(mock_zipfile),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that cache SHA read errors are handled gracefully."""
    hass.config.config_dir = str(tmp_path)

    pr_cache_dir = tmp_path / ".cache" / "frontend" / "development_artifacts"
    frontend_dir = pr_cache_dir / "hass_frontend"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "index.html").write_text("test")
    sha_file = pr_cache_dir / ".sha"
    sha_file.write_text("abc123def456")
    sha_file.chmod(0o000)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    try:
        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect(len(aioclient_mock.mock_calls)).to_equal(1)
        expect("Failed to read cache SHA file" in caplog.text).to_be(True)
    finally:
        sha_file.chmod(0o644)


@test
async def pr_download_session_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of session creation errors."""
    hass.config.config_dir = str(tmp_path)

    with patch(
        "homeassistant.components.frontend.pr_download.async_get_clientsession",
        side_effect=RuntimeError("Session error"),
    ):
        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("Failed to download PR #12345" in caplog.text).to_be(True)


@test.cases(
    test.case(
        "auth",
        exc=GitHubAuthenticationException("Unauthorized"),
        error_message="invalid or expired",
    ),
    test.case(
        "ratelimit",
        exc=GitHubRatelimitException("Rate limit exceeded"),
        error_message="rate limit",
    ),
    test.case(
        "permission",
        exc=GitHubPermissionException("Forbidden"),
        error_message="rate limit",
    ),
    test.case(
        "not_found",
        exc=GitHubNotFoundException("Not found"),
        error_message="does not exist",
    ),
    test.case(
        "api_error",
        exc=GitHubException("API error"),
        error_message="api error",
    ),
)
async def pr_download_github_errors(
    exc: Exception,
    error_message: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of various GitHub API errors."""
    hass.config.config_dir = str(tmp_path)

    with patch(
        "homeassistant.components.frontend.pr_download.GitHubAPI"
    ) as mock_gh_class:
        mock_client = AsyncMock()
        mock_gh_class.return_value = mock_client
        mock_client.generic.side_effect = exc

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect(error_message in caplog.text.lower()).to_be(True)
        expect("Failed to download PR #12345" in caplog.text).to_be(True)


@test.cases(
    test.case(
        "auth",
        exc=GitHubAuthenticationException("Unauthorized"),
        error_message="invalid or expired",
    ),
    test.case(
        "ratelimit",
        exc=GitHubRatelimitException("Rate limit exceeded"),
        error_message="rate limit",
    ),
    test.case(
        "permission",
        exc=GitHubPermissionException("Forbidden"),
        error_message="rate limit",
    ),
    test.case(
        "api_error",
        exc=GitHubException("API error"),
        error_message="api error",
    ),
)
async def pr_download_artifact_search_github_errors(
    exc: Exception,
    error_message: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of GitHub API errors during artifact search."""
    hass.config.config_dir = str(tmp_path)

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

        async def generic_side_effect(endpoint, **_kwargs):
            if "pulls" in endpoint:
                return pr_response
            raise exc

        mock_client.generic.side_effect = generic_side_effect

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect(error_message in caplog.text.lower()).to_be(True)
        expect("Failed to download PR #12345" in caplog.text).to_be(True)


@test
async def pr_download_artifact_not_found(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling when artifact is not found."""
    hass.config.config_dir = str(tmp_path)

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
        workflow_response.data = {"workflow_runs": []}

        async def generic_side_effect(endpoint, **kwargs):
            if "pulls" in endpoint:
                return pr_response
            if "workflows" in endpoint:
                return workflow_response
            raise ValueError(f"Unexpected endpoint: {endpoint}")

        mock_client.generic.side_effect = generic_side_effect

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("No 'frontend-build' artifact found" in caplog.text).to_be(True)


@test
async def pr_download_http_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of HTTP download errors."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        exc=ClientError("Download failed"),
    )

    config = {
        DOMAIN: {
            "development_pr": 12345,
            "github_token": "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect("Failed to download PR #12345" in caplog.text).to_be(True)


@test.cases(
    test.case("401", status=401, error_message="invalid or expired"),
    test.case("403", status=403, error_message="rate limit"),
    test.case("500", status=500, error_message="http 500"),
)
async def pr_download_http_status_errors(
    status: int,
    error_message: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of HTTP status errors during artifact download."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        status=status,
    )

    config = {
        DOMAIN: {
            "development_pr": 12345,
            "github_token": "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect(error_message in caplog.text.lower()).to_be(True)
    expect("Failed to download PR #12345" in caplog.text).to_be(True)


@test
async def pr_download_timeout_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of timeout during artifact download."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        exc=TimeoutError("Connection timed out"),
    )

    config = {
        DOMAIN: {
            "development_pr": 12345,
            "github_token": "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect("timeout" in caplog.text.lower()).to_be(True)
    expect("Failed to download PR #12345" in caplog.text).to_be(True)


@test
async def pr_download_bad_zip_file(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of corrupted zip file."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"not a valid zip file",
    )

    config = {
        DOMAIN: {
            "development_pr": 12345,
            "github_token": "test_token",
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    expect("Failed to download PR #12345" in caplog.text).to_be(True)
    expect("corrupted or invalid" in caplog.text.lower()).to_be(True)


@test
async def pr_download_zip_bomb_too_many_files(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that zip bombs with too many files are rejected."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    with patch("zipfile.ZipFile") as mock_zip:
        mock_zip_instance = MagicMock()
        mock_info = MagicMock()
        mock_info.file_size = 100
        mock_zip_instance.infolist.return_value = [mock_info] * 55000
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("Failed to download PR #12345" in caplog.text).to_be(True)
        expect("too many files" in caplog.text.lower()).to_be(True)


@test
async def pr_download_zip_bomb_too_large(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that zip bombs with excessive uncompressed size are rejected."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    with patch("zipfile.ZipFile") as mock_zip:
        mock_zip_instance = MagicMock()
        mock_info = MagicMock()
        mock_info.file_size = 2 * 1024 * 1024 * 1024
        mock_zip_instance.infolist.return_value = [mock_info]
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("Failed to download PR #12345" in caplog.text).to_be(True)
        expect("too large" in caplog.text.lower()).to_be(True)


@test
async def pr_download_extraction_os_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    tmp_path: Path = Depends(tmp_path_fixture),
    mock_github_api: AsyncMock = Depends(mock_github_api),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test handling of OS errors during extraction."""
    hass.config.config_dir = str(tmp_path)

    aioclient_mock.get(
        "https://api.github.com/artifact/download",
        content=b"fake zip data",
    )

    with patch("zipfile.ZipFile") as mock_zip:
        mock_zip_instance = MagicMock()
        mock_info = MagicMock()
        mock_info.file_size = 100
        mock_zip_instance.infolist.return_value = [mock_info]
        mock_zip_instance.extractall.side_effect = OSError("Disk full")
        mock_zip.return_value.__enter__.return_value = mock_zip_instance

        config = {
            DOMAIN: {
                "development_pr": 12345,
                "github_token": "test_token",
            }
        }

        expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
        await hass.async_block_till_done()

        expect("Failed to download PR #12345" in caplog.text).to_be(True)
        expect("failed to extract" in caplog.text.lower()).to_be(True)
