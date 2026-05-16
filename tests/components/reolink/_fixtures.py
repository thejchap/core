"""Tryke fixtures for Reolink tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from reolink_aio.api import Chime
from reolink_aio.exceptions import ReolinkError
from tryke import Depends, fixture

from homeassistant.components.reolink.config_flow import DEFAULT_PROTOCOL
from homeassistant.components.reolink.const import (
    CONF_BC_ONLY,
    CONF_BC_PORT,
    CONF_SUPPORTS_PRIVACY_MODE,
    CONF_USE_HTTPS,
    DOMAIN,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac

from .conftest import (
    TEST_BC_PORT,
    TEST_CAM_MODEL,
    TEST_CAM_NAME,
    TEST_HOST,
    TEST_HOST_MODEL,
    TEST_ITEM_NUMBER,
    TEST_MAC,
    TEST_MAC_CAM,
    TEST_NVR_NAME,
    TEST_PASSWORD,
    TEST_PORT,
    TEST_PRIVACY,
    TEST_UID,
    TEST_UID_CAM,
    TEST_USE_HTTPS,
    TEST_USERNAME,
    _init_host_mock,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def reolink_host_class() -> Generator[MagicMock]:
    """Mock reolink connection and return both the host_mock and host_mock_class."""
    with patch(
        "homeassistant.components.reolink.host.Host", autospec=False
    ) as host_mock_class:
        _init_host_mock(host_mock_class.return_value)
        yield host_mock_class


@fixture
def reolink_host(
    reolink_host_class: MagicMock = Depends(reolink_host_class),
) -> MagicMock:
    """Mock reolink Host class."""
    return reolink_host_class.return_value


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Add the reolink mock config entry to hass."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=format_mac(TEST_MAC),
        data={
            CONF_HOST: TEST_HOST,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_PORT: TEST_PORT,
            CONF_USE_HTTPS: TEST_USE_HTTPS,
            CONF_SUPPORTS_PRIVACY_MODE: TEST_PRIVACY,
            CONF_BC_PORT: TEST_BC_PORT,
            CONF_BC_ONLY: False,
        },
        options={
            CONF_PROTOCOL: DEFAULT_PROTOCOL,
        },
        title=TEST_NVR_NAME,
    )
    config_entry.add_to_hass(hass)
    return config_entry
