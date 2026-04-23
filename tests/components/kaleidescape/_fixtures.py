"""Tryke fixtures for Kaleidescape integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from kaleidescape import Dispatcher
from kaleidescape.device import Automation, Movie, Power, System
from tryke import fixture

from homeassistant.components.kaleidescape.const import DOMAIN
from homeassistant.const import CONF_HOST

from . import MOCK_HOST, MOCK_SERIAL

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.kaleidescape.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_device() -> Generator[MagicMock]:
    """Return a mocked Kaleidescape device."""
    with patch(
        "homeassistant.components.kaleidescape.KaleidescapeDevice", autospec=True
    ) as mock:
        host = MOCK_HOST
        device = mock.return_value
        device.dispatcher = Dispatcher()
        device.host = host
        device.port = 10000
        device.serial_number = MOCK_SERIAL
        device.is_connected = True
        device.is_server_only = False
        device.is_movie_player = True
        device.is_music_player = False
        device.system = System(
            ip_address=host,
            serial_number=MOCK_SERIAL,
            type="Strato",
            protocol=16,
            kos_version="10.4.2-19218",
            friendly_name=f"Device {MOCK_SERIAL}",
            movie_zones=1,
            music_zones=1,
        )
        device.power = Power(state="standby", readiness="disabled", zone=["available"])
        device.movie = Movie()
        device.automation = Automation()
        yield device


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_SERIAL,
        version=1,
        data={CONF_HOST: MOCK_HOST},
    )
