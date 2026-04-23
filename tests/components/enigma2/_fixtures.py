"""Tryke fixtures for Enigma2."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from openwebif.api import OpenWebIfDevice, OpenWebIfServiceEvent, OpenWebIfStatus
from tryke import fixture

from homeassistant.components.enigma2.const import (
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, CONF_VERIFY_SSL

from tests.common import MockConfigEntry, load_json_object_fixture

MAC_ADDRESS = "12:34:56:78:90:ab"

TEST_REQUIRED = {
    CONF_HOST: "1.1.1.1",
    CONF_PORT: DEFAULT_PORT,
    CONF_SSL: DEFAULT_SSL,
    CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL,
}


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN, data=TEST_REQUIRED, unique_id="12:34:56:78:90:ab"
    )


@fixture
def openwebif_device_mock() -> Generator[AsyncMock]:
    """Mock a OpenWebIf device."""
    with (
        patch(
            "homeassistant.components.enigma2.coordinator.OpenWebIfDevice",
            spec=OpenWebIfDevice,
        ) as openwebif_device_mock,
        patch(
            "homeassistant.components.enigma2.config_flow.OpenWebIfDevice",
            new=openwebif_device_mock,
        ),
    ):
        device = openwebif_device_mock.return_value
        device.status = OpenWebIfStatus(currservice=OpenWebIfServiceEvent())
        device.turn_off_to_deep = False
        device.sources = {"Test": "1"}
        device.source_list = list(device.sources.keys())
        device.picon_url = "file:///"
        device.get_about.return_value = load_json_object_fixture(
            "device_about.json", DOMAIN
        )
        device.get_status_info.return_value = load_json_object_fixture(
            "device_statusinfo_on.json", DOMAIN
        )
        device.get_all_bouquets.return_value = {
            "bouquets": [
                [
                    '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet',
                    "Favourites (TV)",
                ]
            ]
        }
        yield device


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
