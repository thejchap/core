"""Tryke fixtures for the Seko PoolDose integration."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from pooldose.request_status import RequestStatus
from tryke import Depends, fixture

from homeassistant.components.pooldose.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import (
    MockConfigEntry,
    async_load_json_object_fixture,
    load_json_object_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.pooldose.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
async def device_info(
    hass: HomeAssistant = Depends(hass_fixture),
) -> dict[str, Any]:
    """Return the device info from the fixture."""
    return await async_load_json_object_fixture(hass, "deviceinfo.json", DOMAIN)


@fixture
def mock_pooldose_client(
    info: dict[str, Any] = Depends(device_info),
) -> Generator[MagicMock]:
    """Mock a PooldoseClient for end-to-end testing."""
    with (
        patch(
            "homeassistant.components.pooldose.config_flow.PooldoseClient",
            autospec=True,
        ) as mock_client_class,
        patch(
            "homeassistant.components.pooldose.PooldoseClient", new=mock_client_class
        ),
    ):
        client = mock_client_class.return_value
        client.device_info = info
        client.connect.return_value = RequestStatus.SUCCESS
        client.check_apiversion_supported.return_value = (RequestStatus.SUCCESS, {})
        instant_values_data = load_json_object_fixture("instantvalues.json", DOMAIN)
        client.instant_values_structured.return_value = (
            RequestStatus.SUCCESS,
            instant_values_data,
        )
        client.set_switch = AsyncMock(return_value=RequestStatus.SUCCESS)
        client.set_select = AsyncMock(return_value=RequestStatus.SUCCESS)
        client.is_connected = True
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
def mock_config_entry(
    info: dict[str, Any] = Depends(device_info),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Pool Device",
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100"},
        unique_id=info["SERIAL_NUMBER"],
        entry_id="01JG00V55WEVTJ0CJHM0GAD7PC",
    )
