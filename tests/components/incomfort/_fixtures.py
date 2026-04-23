"""Tryke fixtures for Intergas InComfort integration."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from incomfortclient import DisplayCode
from tryke import fixture

from homeassistant.components.incomfort.const import DOMAIN

from tests.common import MockConfigEntry

MOCK_CONFIG = {
    "host": "192.168.1.12",
    "username": "admin",
    "password": "verysecret",
}

MOCK_CONFIG_DHCP = {
    "username": "admin",
    "password": "verysecret",
}

MOCK_HEATER_STATUS = {
    "display_code": DisplayCode.STANDBY,
    "display_text": "standby",
    "fault_code": None,
    "is_burning": False,
    "is_failed": False,
    "is_pumping": False,
    "is_tapping": False,
    "heater_temp": 35.34,
    "tap_temp": 30.21,
    "pressure": 1.86,
    "serial_no": "c0ffeec0ffee",
    "nodenr": 249,
    "rf_message_rssi": 30,
    "rfstatus_cntr": 0,
}


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.incomfort.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_entry_data() -> dict[str, Any]:
    """Mock config entry data."""
    return MOCK_CONFIG


@fixture
def mock_config_entry(
    mock_entry_data: dict[str, Any] = None,
) -> MockConfigEntry:
    """Mock a config entry setup for incomfort integration."""
    data = mock_entry_data if mock_entry_data is not None else MOCK_CONFIG
    return MockConfigEntry(domain=DOMAIN, data=data, options=None)


@fixture
def mock_heater_status() -> dict[str, Any]:
    """Mock heater status."""
    return dict(MOCK_HEATER_STATUS)


@fixture
def mock_room_status() -> dict[str, Any]:
    """Mock room status."""
    return {"room_temp": 21.42, "setpoint": 18.0, "override": 18.0}


@fixture
def mock_incomfort(
    mock_heater_status: dict[str, Any] = None,
    mock_room_status: dict[str, Any] = None,
) -> Generator[MagicMock]:
    """Mock the InComfort gateway client."""
    heater_status = mock_heater_status if mock_heater_status is not None else dict(MOCK_HEATER_STATUS)
    room_status = mock_room_status if mock_room_status is not None else {
        "room_temp": 21.42,
        "setpoint": 18.0,
        "override": 18.0,
    }

    class MockRoom:
        def __init__(self) -> None:
            self.room_no = 1
            self.status = room_status
            self.set_override = MagicMock()

        @property
        def override(self) -> float:
            return room_status["override"]

        @property
        def room_temp(self) -> float:
            return room_status["room_temp"]

        @property
        def setpoint(self) -> float:
            return room_status["setpoint"]

    class MockHeater:
        def __init__(self) -> None:
            self.serial_no = "c0ffeec0ffee"

        async def update(self) -> None:
            self.status = heater_status
            for key, value in heater_status.items():
                setattr(self, key, value)
            self.rooms = [MockRoom()]

    with patch(
        "homeassistant.components.incomfort.coordinator.InComfortGateway", MagicMock()
    ) as patch_gateway:
        patch_gateway().heaters = AsyncMock()
        patch_gateway().heaters.return_value = [MockHeater()]
        patch_gateway().mock_heater_status = heater_status
        patch_gateway().mock_room_status = room_status
        yield patch_gateway
