"""Tryke fixtures for the Mitsubishi Comfort integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from mitsubishi_comfort import DeviceInfo
from tryke import Depends, fixture

from homeassistant.components.mitsubishi_comfort.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry

MOCK_USERNAME = "test@test.com"
MOCK_PASSWORD = "testpass"


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry and async_unload_entry."""
    with (
        patch(
            "homeassistant.components.mitsubishi_comfort.async_setup_entry",
            return_value=True,
        ) as mock,
        patch(
            "homeassistant.components.mitsubishi_comfort.async_unload_entry",
            return_value=True,
        ),
    ):
        yield mock


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
        unique_id="user-12345",
    )


@fixture
def mock_device_info() -> DeviceInfo:
    """Return a mock DeviceInfo."""
    return DeviceInfo(
        serial="SERIAL001",
        label="Living Room",
        address="192.168.1.100",
        mac="AA:BB:CC:DD:EE:FF",
        unit_type="ductless",
        password="dGVzdHBhc3M=",
        crypto_serial="0102030405060708090a",
    )


@fixture
def mock_cloud_account(
    device_info: DeviceInfo = Depends(mock_device_info),
) -> Generator[AsyncMock]:
    """Mock MitsubishiCloudAccount for both main code and config flow."""
    with (
        patch(
            "homeassistant.components.mitsubishi_comfort.MitsubishiCloudAccount",
            autospec=True,
        ) as mock_cls,
        patch(
            "homeassistant.components.mitsubishi_comfort.config_flow.MitsubishiCloudAccount",
            new=mock_cls,
        ),
    ):
        account = mock_cls.return_value
        account.login.return_value = None
        account.discover_devices.return_value = {"SERIAL001": device_info}
        account.get_passwords_via_websocket.return_value = {}
        account.user_id = "user-12345"
        yield account
