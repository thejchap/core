"""Tryke fixtures for frontend tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp.test_utils import TestClient
from tryke import Depends, fixture

from homeassistant.components.frontend import (
    CONF_EXTRA_JS_URL_ES5,
    CONF_EXTRA_MODULE_URL,
    CONF_THEMES,
    DOMAIN,
)
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    aiohttp_client as aiohttp_client_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.typing import ClientSessionGenerator, MockHAClientWebSocket

MOCK_THEMES = {
    "happy": {"primary-color": "red", "app-header-background-color": "blue"},
    "dark": {"primary-color": "black"},
    "light_only": {
        "primary-color": "blue",
        "modes": {
            "light": {"secondary-color": "black"},
        },
    },
    "dark_only": {
        "primary-color": "blue",
        "modes": {
            "dark": {"secondary-color": "white"},
        },
    },
    "light_and_dark": {
        "primary-color": "blue",
        "modes": {
            "light": {"secondary-color": "black"},
            "dark": {"secondary-color": "white"},
        },
    },
}

CONFIG_THEMES = {DOMAIN: {CONF_THEMES: MOCK_THEMES}}


@fixture
async def ignore_frontend_deps(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Frontend dependencies."""
    frontend = await async_get_integration(hass, "frontend")
    for dep in frontend.dependencies:
        if dep not in ("http", "websocket_api"):
            hass.config.components.add(dep)


@fixture
async def frontend(
    hass: HomeAssistant = Depends(hass_fixture),
    ignore_frontend_deps: None = Depends(ignore_frontend_deps),
) -> None:
    """Frontend setup."""
    assert await async_setup_component(hass, "frontend", {})


@fixture
async def frontend_themes(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Frontend setup with themes."""
    assert await async_setup_component(hass, "frontend", CONFIG_THEMES)


@fixture
async def mock_http_client(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    frontend: None = Depends(frontend),
) -> TestClient:
    """Start the Home Assistant HTTP component."""
    return await aiohttp_client(hass.http.app)


@fixture
async def themes_ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fixture),
    frontend_themes: None = Depends(frontend_themes),
) -> MockHAClientWebSocket:
    """Start the Home Assistant HTTP component."""
    return await hass_ws_client(hass)


@fixture
async def ws_client(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: ClientSessionGenerator = Depends(hass_ws_client_fixture),
    frontend: None = Depends(frontend),
) -> MockHAClientWebSocket:
    """Start the Home Assistant HTTP component."""
    return await hass_ws_client(hass)


@fixture
async def mock_http_client_with_extra_js(
    hass: HomeAssistant = Depends(hass_fixture),
    aiohttp_client: ClientSessionGenerator = Depends(aiohttp_client_fixture),
    ignore_frontend_deps: None = Depends(ignore_frontend_deps),
) -> TestClient:
    """Start the Home Assistant HTTP component."""
    assert await async_setup_component(
        hass,
        "frontend",
        {
            DOMAIN: {
                CONF_EXTRA_MODULE_URL: ["/local/my_module.js"],
                CONF_EXTRA_JS_URL_ES5: ["/local/my_es5.js"],
            }
        },
    )
    return await aiohttp_client(hass.http.app)


@fixture
def mock_onboarded() -> Generator[None]:
    """Mock that we're onboarded."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded", return_value=True
    ):
        yield


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
