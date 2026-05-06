"""Tryke fixtures for Fibaro."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.fibaro import CONF_IMPORT_PLUGINS, DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture

TEST_SERIALNUMBER = "HC2-111111"
TEST_NAME = "my_fibaro_home_center"
TEST_URL = "http://192.168.1.1/api/"
TEST_USERNAME = "user"
TEST_PASSWORD = "password"
TEST_VERSION = "4.360"
TEST_MODEL = "HC3"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.fibaro.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@fixture
def mock_fibaro_client() -> Generator[Mock]:
    """Return a mocked FibaroClient."""
    info_mock = Mock()
    info_mock.serial_number = TEST_SERIALNUMBER
    info_mock.hc_name = TEST_NAME
    info_mock.current_version = TEST_VERSION
    info_mock.platform = TEST_MODEL
    info_mock.manufacturer_name = "Fibaro"
    info_mock.model_name = "Home Center 2"
    info_mock.mac_address = "00:22:4d:b7:13:24"

    with patch(
        "homeassistant.components.fibaro.FibaroClient", autospec=True
    ) as fibaro_client_mock:
        client = fibaro_client_mock.return_value
        client.connect_with_credentials.return_value = info_mock
        client.read_info.return_value = info_mock
        client.read_rooms.return_value = []
        client.read_scenes.return_value = []
        client.read_devices.return_value = []
        client.register_update_handler.return_value = None
        client.unregister_update_handler.return_value = None
        client.frontend_url.return_value = TEST_URL.removesuffix("/api/")
        yield client


@fixture
def mock_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_IMPORT_PLUGINS: True,
        },
    )
    entry.add_to_hass(hass)
    return entry
