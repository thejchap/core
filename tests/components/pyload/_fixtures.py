"""Tryke fixtures for pyLoad tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from pyloadapi.types import StatusServerResponse
from tryke import Depends, fixture

from homeassistant.components.pyload.const import DEFAULT_NAME, DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers.service_info.hassio import HassioServiceInfo

from tests.common import MockConfigEntry

USER_INPUT = {
    CONF_URL: "https://pyload.local:8000/prefix",
    CONF_PASSWORD: "test-password",
    CONF_USERNAME: "test-username",
    CONF_VERIFY_SSL: False,
}

REAUTH_INPUT = {
    CONF_PASSWORD: "new-password",
    CONF_USERNAME: "new-username",
}

NEW_INPUT = {
    CONF_URL: "https://pyload.local:8000/prefix",
    CONF_PASSWORD: "new-password",
    CONF_USERNAME: "new-username",
    CONF_VERIFY_SSL: False,
}


ADDON_DISCOVERY_INFO = {
    "addon": "pyLoad-ng",
    CONF_URL: "http://539df76c-pyload-ng:8000/",
    CONF_USERNAME: "pyload",
    CONF_PASSWORD: "pyload",
}

ADDON_SERVICE_INFO = HassioServiceInfo(
    config=ADDON_DISCOVERY_INFO,
    name="pyLoad-ng Addon",
    slug="p539df76c_pyload-ng",
    uuid="1234",
)


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.pyload.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_pyloadapi() -> Generator[MagicMock]:
    """Mock PyLoadAPI."""
    with (
        patch(
            "homeassistant.components.pyload.PyLoadAPI", autospec=True
        ) as mock_client,
        patch(
            "homeassistant.components.pyload.config_flow.PyLoadAPI", new=mock_client
        ),
    ):
        client = mock_client.return_value
        client.username = "username"
        client.api_url = "https://pyload.local:8000/"

        client.get_status.return_value = StatusServerResponse(
            {
                "pause": False,
                "active": 1,
                "queue": 6,
                "total": 37,
                "speed": 5405963.0,
                "download": True,
                "reconnect": False,
                "captcha": False,
            }
        )
        client.version.return_value = "0.5.0"
        client.free_space.return_value = 99999999999
        yield client


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def mock_async_zeroconf(
    _zc: MagicMock = Depends(mock_zeroconf),
) -> Generator[MagicMock]:
    """Mock AsyncZeroconf."""
    from zeroconf import DNSCache, Zeroconf  # noqa: PLC0415
    from zeroconf.asyncio import AsyncZeroconf  # noqa: PLC0415

    with patch(
        "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
    ) as mock_aiozc:
        zc = mock_aiozc.return_value
        zc.async_unregister_service = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.zeroconf = Mock(spec=Zeroconf)
        zc.zeroconf.async_wait_for_start = AsyncMock()
        zc.zeroconf.cache = DNSCache()
        zc.zeroconf.done = False
        zc.async_close = AsyncMock()
        zc.ha_async_close = AsyncMock()
        yield zc


@fixture
def config_entry() -> MockConfigEntry:
    """Mock pyLoad configuration entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_NAME,
        data=USER_INPUT,
        entry_id="XXXXXXXXXXXXXX",
    )


@fixture
def config_entry_migrate() -> MockConfigEntry:
    """Mock pyLoad configuration entry for migration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=DEFAULT_NAME,
        data={
            CONF_HOST: "pyload.local",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 8000,
            CONF_SSL: True,
            CONF_USERNAME: "test-username",
            CONF_VERIFY_SSL: False,
        },
        version=1,
        minor_version=0,
        entry_id="XXXXXXXXXXXXXX",
    )
