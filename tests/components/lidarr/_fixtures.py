"""Tryke fixtures for Lidarr tests."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Generator
from http import HTTPStatus

from aiohttp.client_exceptions import ClientError
from aiopyarr.lidarr_client import LidarrClient
from tryke import Depends, fixture

from homeassistant.components.lidarr.const import DOMAIN
from homeassistant.const import (
    CONF_API_KEY,
    CONF_URL,
    CONF_VERIFY_SSL,
    CONTENT_TYPE_JSON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import aioclient_mock as aioclient_mock_fixture, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

URL = "http://127.0.0.1:8668"
API_KEY = "1234567890abcdef1234567890abcdef"
_client = LidarrClient(session=async_get_clientsession, api_token=API_KEY, url=URL)
API_URL = f"{URL}/api/{_client._host.api_ver}"

MOCK_INPUT = {CONF_URL: URL, CONF_VERIFY_SSL: False}

CONF_DATA = MOCK_INPUT | {CONF_API_KEY: API_KEY}

type ComponentSetup = Callable[[], Awaitable[None]]


def _mock_error(
    aioclient_mock: AiohttpClientMocker, status: HTTPStatus | None = None
) -> None:
    """Mock an error."""
    if status:
        aioclient_mock.get(f"{API_URL}/queue", status=status)
        aioclient_mock.get(f"{API_URL}/rootfolder", status=status)
        aioclient_mock.get(f"{API_URL}/system/status", status=status)
        aioclient_mock.get(f"{API_URL}/wanted/missing", status=status)
        aioclient_mock.get(f"{API_URL}/album", status=status)
    aioclient_mock.get(f"{API_URL}/queue", exc=ClientError)
    aioclient_mock.get(f"{API_URL}/rootfolder", exc=ClientError)
    aioclient_mock.get(f"{API_URL}/system/status", exc=ClientError)
    aioclient_mock.get(f"{API_URL}/wanted/missing", exc=ClientError)
    aioclient_mock.get(f"{API_URL}/album", exc=ClientError)


@fixture
def cannot_connect(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Mock cannot connect error."""
    _mock_error(aioclient_mock, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@fixture
def invalid_auth(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Mock invalid authorization error."""
    _mock_error(aioclient_mock, status=HTTPStatus.UNAUTHORIZED)


@fixture
def wrong_app(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Mock Lidarr wrong app."""
    aioclient_mock.get(
        f"{URL}/initialize.js",
        text=load_fixture("lidarr/initialize-wrong.js"),
        headers={"Content-Type": "application/javascript"},
    )


@fixture
def zeroconf_failed(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Mock Lidarr zero configuration failure."""
    aioclient_mock.get(
        f"{URL}/initialize.js",
        text="login-failed",
        headers={"Content-Type": "application/javascript"},
    )


@fixture
def unknown(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Mock Lidarr unknown error."""
    aioclient_mock.get(
        f"{URL}/initialize.js",
        text="something went wrong",
        headers={"Content-Type": "application/javascript"},
    )


@fixture
def connection(
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
) -> None:
    """Mock Lidarr connection."""
    aioclient_mock.get(
        f"{URL}/initialize.js",
        text=load_fixture("lidarr/initialize.js"),
        headers={"Content-Type": "application/javascript"},
    )
    aioclient_mock.get(
        f"{API_URL}/system/status",
        text=load_fixture("lidarr/system-status.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{API_URL}/queue",
        text=load_fixture("lidarr/queue.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{API_URL}/wanted/missing",
        text=load_fixture("lidarr/wanted-missing.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{API_URL}/album",
        text=load_fixture("lidarr/album.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{API_URL}/rootfolder",
        text=load_fixture("lidarr/rootfolder-linux.json"),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )


@fixture
def config_entry() -> MockConfigEntry:
    """Create Lidarr entry in Home Assistant."""
    return MockConfigEntry(domain=DOMAIN, data=CONF_DATA)


@fixture
def setup_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry),
) -> Generator[ComponentSetup]:
    """Set up the lidarr integration in Home Assistant."""
    config_entry.add_to_hass(hass)

    async def func() -> None:
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

    yield func
