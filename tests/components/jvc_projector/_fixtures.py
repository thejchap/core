"""Tryke fixtures for JVC Projector integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from jvcprojector import Command, JvcProjectorTimeoutError, command as cmd
from tryke import Depends, fixture

from homeassistant.components.jvc_projector.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.helpers.device_registry import format_mac

from . import MOCK_HOST, MOCK_MAC, MOCK_MODEL, MOCK_PASSWORD, MOCK_PORT

from tests.common import MockConfigEntry

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

    with patch(
        "homeassistant.components.jvc_projector.config_flow.JvcProjector",
        autospec=True,
    ) as mock:
        device = mock.return_value
        device.ip = MOCK_HOST
        device.host = MOCK_HOST
        device.port = MOCK_PORT
        device.mac = MOCK_MAC
        device.model = MOCK_MODEL
        device.get.side_effect = device_get
        device.capabilities.return_value = {}
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
