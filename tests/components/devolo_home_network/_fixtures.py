"""Tryke fixtures for the devolo_home_network integration."""

from collections.abc import Generator
from itertools import cycle
from unittest.mock import MagicMock, patch

from tryke import Depends, fixture

from .const import DISCOVERY_INFO, IP
from .mock import MockDevice

from tests.hass_tryke_helpers import mock_async_zeroconf


@fixture
def mock_device() -> Generator[MockDevice]:
    """Mock connecting to a devolo home network device."""
    device = MockDevice(ip=IP)
    with patch(
        "homeassistant.components.devolo_home_network.Device",
        side_effect=cycle([device]),
    ):
        yield device


@fixture
def info() -> Generator[dict[str, str]]:
    """Mock setup entry and user input."""
    info = {
        "serial_number": DISCOVERY_INFO.properties["SN"],
        "title": DISCOVERY_INFO.properties["Product"],
    }

    with patch(
        "homeassistant.components.devolo_home_network.config_flow.validate_input",
        return_value=info,
    ):
        yield info


@fixture
def devolo_zeroconf(
    _zc: MagicMock = Depends(mock_async_zeroconf),
) -> None:
    """Auto mock zeroconf."""
    return None
