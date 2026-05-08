"""Tryke fixtures for Pure Energie tests."""

from __future__ import annotations

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from gridnet import Device as GridNetDevice, SmartBridge
from tryke import Depends, fixture

from homeassistant.components.pure_energie.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="home",
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.123"},
        unique_id="unique_thingy",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.pure_energie.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_pure_energie_config_flow() -> Generator[MagicMock]:
    """Return a mocked Pure Energie client."""
    with patch(
        "homeassistant.components.pure_energie.config_flow.GridNet", autospec=True
    ) as pure_energie_mock:
        pure_energie = pure_energie_mock.return_value
        pure_energie.device.return_value = GridNetDevice.from_dict(
            json.loads(load_fixture("device.json", DOMAIN))
        )
        yield pure_energie


@fixture
def mock_pure_energie() -> Generator[MagicMock]:
    """Return a mocked Pure Energie client."""
    with patch(
        "homeassistant.components.pure_energie.coordinator.GridNet", autospec=True
    ) as pure_energie_mock:
        pure_energie = pure_energie_mock.return_value
        pure_energie.smartbridge = AsyncMock(
            return_value=SmartBridge.from_dict(
                json.loads(load_fixture("pure_energie/smartbridge.json"))
            )
        )
        pure_energie.device = AsyncMock(
            return_value=GridNetDevice.from_dict(
                json.loads(load_fixture("pure_energie/device.json"))
            )
        )
        yield pure_energie_mock


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_pure_energie: MagicMock = Depends(mock_pure_energie),
) -> MockConfigEntry:
    """Set up the Pure Energie integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


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
