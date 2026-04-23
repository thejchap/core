"""Tryke fixtures for Energenie-Power-Sockets."""

from collections.abc import Generator
from typing import Final
from unittest.mock import AsyncMock, MagicMock, patch

from pyegps.fakes.powerstrip import FakePowerStrip
from tryke import Depends, fixture

from homeassistant.components.energenie_power_sockets.const import (
    CONF_DEVICE_API_ID,
    DOMAIN,
)
from homeassistant.const import CONF_NAME

from tests.common import MockConfigEntry

DEMO_CONFIG_DATA: Final = {
    CONF_NAME: "Unit Test",
    CONF_DEVICE_API_ID: "DYPS:00:11:22",
}


@fixture
def demo_config_data() -> dict:
    """Return valid user input."""
    return {CONF_DEVICE_API_ID: DEMO_CONFIG_DATA[CONF_DEVICE_API_ID]}


@fixture
def valid_config_entry() -> MockConfigEntry:
    """Return a valid egps config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=DEMO_CONFIG_DATA,
        unique_id=DEMO_CONFIG_DATA[CONF_DEVICE_API_ID],
    )


@fixture
def pyegps_device_mock() -> MagicMock:
    """Fixture for a mocked FakePowerStrip."""
    fkObj = FakePowerStrip(
        devId=DEMO_CONFIG_DATA[CONF_DEVICE_API_ID], number_of_sockets=4
    )
    fkObj.release = lambda: None
    fkObj._status = [0, 1, 0, 1]

    usb_device_mock = MagicMock(wraps=fkObj)
    usb_device_mock.get_device_type.return_value = "PowerStrip"
    usb_device_mock.numberOfSockets = 4
    usb_device_mock.device_id = DEMO_CONFIG_DATA[CONF_DEVICE_API_ID]
    usb_device_mock.manufacturer = "Energenie"
    usb_device_mock.name = "MockedUSBDevice"

    return usb_device_mock


@fixture
def mock_get_device(
    pyegps_device_mock: MagicMock = Depends(pyegps_device_mock),
) -> Generator[MagicMock]:
    """Fixture to patch the `get_device` api method."""
    with (
        patch("homeassistant.components.energenie_power_sockets.get_device") as m1,
        patch(
            "homeassistant.components.energenie_power_sockets.config_flow.get_device",
            new=m1,
        ) as mock,
    ):
        mock.return_value = pyegps_device_mock
        yield mock


@fixture
def mock_search_for_devices(
    pyegps_device_mock: MagicMock = Depends(pyegps_device_mock),
) -> Generator[MagicMock]:
    """Fixture to patch the `search_for_devices` api method."""
    with patch(
        "homeassistant.components.energenie_power_sockets.config_flow.search_for_devices",
        return_value=[pyegps_device_mock],
    ) as mock:
        yield mock


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
