"""Tryke fixtures for the zwave_js integration.

Ports the relevant bits of the 1515-line ``conftest.py`` to tryke fixtures.
The shape mirrors ``conftest.py`` but only covers what the migrated tests
actually need:

* ``mock_setup_entry`` / ``mock_unload_entry`` patches.
* ``mock_scan_serial_ports`` autouse fixture (config_flow-local).
* ``mock_usb_serial_by_id`` autouse fixture (config_flow-local).
* ``mock_addon_setup_time`` autouse fixture (config_flow-local).
* ``set_country`` autouse fixture (config_flow-local).
* ``get_server_version`` autouse fixture (zwave_js conftest).

The driver/client/node mock chain (``client``, ``integration``,
all of the per-device state fixtures) is intentionally NOT ported here
yet — the tests that depend on it remain skipped pending a follow-up.
"""

from collections.abc import Generator
import dataclasses
from unittest.mock import AsyncMock, MagicMock, patch

from aiohasupervisor.models import Discovery
from tryke import Depends, fixture
from zwave_js_server.version import VersionInfo

from homeassistant.components.usb import SerialDevice, USBDevice
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Patch ``async_setup_entry`` to short-circuit integration setup."""
    with patch(
        "homeassistant.components.zwave_js.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


@fixture
def mock_unload_entry() -> Generator[AsyncMock]:
    """Patch ``async_unload_entry`` to short-circuit integration teardown."""
    with patch(
        "homeassistant.components.zwave_js.async_unload_entry", return_value=True
    ) as unload_entry:
        yield unload_entry


@fixture
def mock_supervisor() -> Generator[None]:
    """Patch ``is_hassio`` to make the supervisor branch active."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.is_hassio", return_value=True
    ):
        yield


@fixture
def serial_port() -> USBDevice:
    """Return a representative mock serial port.

    Mirrors ``conftest.py``'s ``serial_port`` fixture verbatim so any test
    relying on ``USB_DISCOVERY_INFO`` matching the scan list still works.
    """
    return USBDevice(
        device="/test",
        vid="162E",
        pid="269C",
        serial_number="1234",
        manufacturer="Virtual serial port",
        description="Some serial port",
    )


@fixture
def mock_scan_serial_ports(
    serial_port: USBDevice = Depends(serial_port),
) -> Generator[MagicMock]:
    """Patch ``async_scan_serial_ports`` with a representative fixture set."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.async_scan_serial_ports"
    ) as mock_scan:
        another_port = USBDevice(
            device="/new",
            vid="162E",
            pid="223D",
            serial_number="5678",
            manufacturer="Virtual serial port",
            description="New serial port",
        )

        no_vid_port = SerialDevice(
            device="/no_vid",
            description="Port without vid",
            serial_number="9123",
            manufacturer=None,
        )

        mock_scan.return_value = [serial_port, another_port, no_vid_port]
        yield mock_scan


@fixture
def mock_usb_serial_by_id() -> Generator[MagicMock]:
    """Patch ``usb.get_serial_by_id`` to return its input unchanged."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.usb.get_serial_by_id"
    ) as mock_get_serial_by_id:
        mock_get_serial_by_id.side_effect = lambda x: x
        yield mock_get_serial_by_id


@fixture
def mock_addon_setup_time() -> Generator[None]:
    """Drop the add-on setup wait time to zero."""
    with patch(
        "homeassistant.components.zwave_js.config_flow.ADDON_SETUP_TIMEOUT", new=0
    ):
        yield


@fixture
def mock_get_server_version() -> Generator[AsyncMock]:
    """Patch ``get_server_version`` with a usable VersionInfo.

    Equivalent to the autouse ``get_server_version`` in conftest.py.
    Tests that need a different home_id mutate the returned mock's
    ``return_value`` (which is a frozen dataclass — use
    :func:`dataclasses.replace`).
    """
    version_info = VersionInfo(
        driver_version="mock-driver-version",
        server_version="mock-server-version",
        home_id=1234,
        min_schema_version=0,
        max_schema_version=1,
    )
    with patch(
        "homeassistant.components.zwave_js.helpers.get_server_version",
        return_value=version_info,
    ) as mock_version:
        yield mock_version


@fixture
def set_country(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[None]:
    """Force the test ``HomeAssistant`` instance into a known country.

    Ports the autouse ``set_country`` fixture in conftest.py — required so
    that flows do not prompt for a country selection mid-test.
    """
    original_country = hass.config.country
    hass.config.country = "US"
    yield
    hass.config.country = original_country


def _set_home_id(get_server_version: AsyncMock, home_id: int) -> None:
    """Update the mocked server version's home_id (frozen dataclass)."""
    get_server_version.return_value = dataclasses.replace(
        get_server_version.return_value, home_id=home_id
    )


__all__ = [
    "_set_home_id",
    "mock_addon_setup_time",
    "mock_get_server_version",
    "mock_scan_serial_ports",
    "mock_setup_entry",
    "mock_supervisor",
    "mock_unload_entry",
    "mock_usb_serial_by_id",
    "serial_port",
    "set_country",
]
