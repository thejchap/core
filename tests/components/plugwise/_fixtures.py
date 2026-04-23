"""Tryke fixtures for Plugwise tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from munch import Munch
from packaging.version import Version
from tryke import Depends, fixture

from homeassistant.components.plugwise.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture


def build_smile(**attrs: Any) -> Munch:
    """Build smile Munch from provided attributes."""
    smile = Munch()
    for k, v in attrs.items():
        setattr(smile, k, v)
    return smile


def _read_json(environment: str, call: str) -> dict[str, Any]:
    """Decode the json data."""
    return json.loads(load_fixture(f"plugwise/{environment}/{call}.json"))


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="My Plugwise",
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "AA:BB:CC:DD:EE:FF",
            CONF_PASSWORD: "test-password",
            CONF_PORT: 80,
            CONF_USERNAME: "smile",
        },
        unique_id="smile98765",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.plugwise.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_smile_config_flow() -> Generator[MagicMock]:
    """Return a mocked Smile client."""
    with patch(
        "homeassistant.components.plugwise.config_flow.Smile",
        autospec=True,
    ) as api_mock:
        api = api_mock.return_value

        api.connect.return_value = Version("4.3.2")
        api.smile = build_smile(
            hostname="smile12345",
            model="Test Model",
            model_id="Test Model ID",
            name="Test Smile Name",
            version="4.3.2",
        )

        yield api


@fixture
def mock_smile_adam() -> Generator[MagicMock]:
    """Create a Mock Adam environment for testing exceptions."""
    chosen_env = "m_adam_multiple_devices_per_zone"
    data = _read_json(chosen_env, "data")
    with (
        patch(
            "homeassistant.components.plugwise.coordinator.Smile", autospec=True
        ) as api_mock,
        patch(
            "homeassistant.components.plugwise.config_flow.Smile",
            new=api_mock,
        ),
    ):
        api = api_mock.return_value

        api.async_update.return_value = data
        api.cooling_present = False
        api.connect.return_value = Version("3.0.15")
        api.gateway_id = "fe799307f1624099878210aa0b9f1475"
        api.heater_id = "90986d591dcd426cae3ec3e8111ff730"
        api.reboot = True
        api.smile = build_smile(
            hostname="smile98765",
            model="Gateway",
            model_id="smile_open_therm",
            name="Adam",
            type="thermostat",
            version="3.0.15",
        )

        yield api


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


_mock_config_entry = mock_config_entry


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(_mock_config_entry),
) -> AsyncGenerator[MockConfigEntry]:
    """Set up the Plugwise integration for testing."""
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    yield entry
