"""Tryke fixtures for the jvc_projector integration."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from jvcprojector import Command, JvcProjectorTimeoutError, command as cmd
from tryke import Depends, fixture

from homeassistant.components.jvc_projector.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac

from . import MOCK_HOST, MOCK_MAC, MOCK_MODEL, MOCK_PASSWORD, MOCK_PORT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

FIXTURES: dict[str, dict[type[Command], str | type[Exception]]] = {
    "standby": {
        cmd.MacAddress: MOCK_MAC,
        cmd.ModelName: MOCK_MODEL,
        cmd.Power: "standby",
        cmd.Input: "hdmi1",
        cmd.Signal: "none",
        cmd.LightTime: "100",
        cmd.Source: JvcProjectorTimeoutError,
        cmd.Hdr: JvcProjectorTimeoutError,
        cmd.HdrProcessing: JvcProjectorTimeoutError,
        cmd.EShift: JvcProjectorTimeoutError,
    },
    "on": {
        cmd.MacAddress: MOCK_MAC,
        cmd.ModelName: MOCK_MODEL,
        cmd.Power: "on",
        cmd.Input: "hdmi1",
        cmd.Signal: "signal",
        cmd.LightTime: "100",
        cmd.Source: "4k",
        cmd.Hdr: "hdr",
        cmd.HdrProcessing: "static",
        cmd.EShift: "on",
    },
}

CAPABILITIES = {
    cmd.Power.name: {
        "name": cmd.Power.name,
        "parameter": {"read": {"0": "standby", "1": "on"}},
    },
    cmd.Input.name: {
        "name": cmd.Input.name,
        "parameter": {"read": {"6": "hdmi1", "7": "hdmi2"}},
    },
    cmd.Signal.name: {
        "name": cmd.Signal.name,
        "parameter": {"read": {"0": "none", "1": "signal"}},
    },
    cmd.Source.name: {
        "name": cmd.Source.name,
        "parameter": {"read": {"0": "4k"}},
    },
    cmd.Hdr.name: {
        "name": cmd.Hdr.name,
        "parameter": {"read": {"0": "sdr", "1": "hdr"}},
    },
    cmd.HdrProcessing.name: {
        "name": cmd.HdrProcessing.name,
        "parameter": {"read": {"0": "hdr", "1": "static"}},
    },
    cmd.LightTime.name: {
        "name": cmd.LightTime.name,
        "parameter": "empty",
    },
    cmd.EShift.name: {
        "name": cmd.EShift.name,
        "parameter": {"read": {"0": "off", "1": "on"}},
    },
}

# Default config-flow target (parametrize indirect overrides this in pytest;
# tryke port hard-codes the config_flow target since it's used by every test).
TARGET = "homeassistant.components.jvc_projector.config_flow.JvcProjector"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.jvc_projector.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_device() -> Generator[MagicMock]:
    """Return a mocked JVC Projector device."""
    fixture_data = FIXTURES["on"].copy()

    async def device_get(command) -> str:
        if command in fixture_data:
            value = fixture_data[command]
            if isinstance(value, type) and issubclass(value, Exception):
                raise value
            return value
        raise ValueError(f"Test fixture failure; unexpected command {command}")

    with patch(TARGET, autospec=True) as mock:
        device = mock.return_value
        device.ip = MOCK_HOST
        device.host = MOCK_HOST
        device.port = MOCK_PORT
        device.mac = MOCK_MAC
        device.model = MOCK_MODEL
        device.get.side_effect = device_get
        device.capabilities.return_value = CAPABILITIES
        yield device


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=format_mac(MOCK_MAC),
        version=1,
        data={
            CONF_HOST: MOCK_HOST,
            CONF_PORT: MOCK_PORT,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )


@fixture
async def mock_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_device: MagicMock = Depends(mock_device),
) -> AsyncGenerator[MockConfigEntry]:
    """Return a mock ConfigEntry setup for the integration.

    Note: pytest version uses ``mock_device`` against the config-flow target
    via indirect parametrize. Under tryke we keep the integration target
    patch separately so the entry can actually load.
    """
    with (
        patch(
            "homeassistant.components.jvc_projector.JvcProjector",
            autospec=True,
        ) as setup_mock,
        patch("homeassistant.components.jvc_projector.coordinator.TIMEOUT_RETRIES", 2),
        patch("homeassistant.components.jvc_projector.coordinator.TIMEOUT_SLEEP", 0.1),
    ):
        device = setup_mock.return_value
        device.ip = MOCK_HOST
        device.host = MOCK_HOST
        device.port = MOCK_PORT
        device.mac = MOCK_MAC
        device.model = MOCK_MODEL

        async def device_get(command):
            value = FIXTURES["on"].get(command)
            if value is None:
                raise ValueError(f"Test fixture failure; unexpected command {command}")
            if isinstance(value, type) and issubclass(value, Exception):
                raise value
            return value

        device.get.side_effect = device_get
        device.capabilities.return_value = CAPABILITIES
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        yield mock_config_entry
