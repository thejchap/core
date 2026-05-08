"""Tryke fixtures for the Panasonic Viera integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

from panasonic_viera import TV_TYPE_ENCRYPTED, TV_TYPE_NONENCRYPTED
from tryke import fixture

from homeassistant.components.panasonic_viera.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_MANUFACTURER,
    ATTR_MODEL_NUMBER,
    ATTR_UDN,
    CONF_APP_ID,
    CONF_ENCRYPTION_KEY,
    CONF_ON_ACTION,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL_NUMBER,
    DEFAULT_NAME,
    DEFAULT_PORT,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.typing import UNDEFINED, UndefinedType

MOCK_BASIC_DATA = {
    CONF_HOST: "0.0.0.0",
    CONF_NAME: DEFAULT_NAME,
}

MOCK_CONFIG_DATA = {
    **MOCK_BASIC_DATA,
    CONF_PORT: DEFAULT_PORT,
    CONF_ON_ACTION: None,
}

MOCK_ENCRYPTION_DATA = {
    CONF_APP_ID: "mock-app-id",
    CONF_ENCRYPTION_KEY: "mock-encryption-key",
}

MOCK_DEVICE_INFO = {
    ATTR_FRIENDLY_NAME: DEFAULT_NAME,
    ATTR_MANUFACTURER: DEFAULT_MANUFACTURER,
    ATTR_MODEL_NUMBER: DEFAULT_MODEL_NUMBER,
    ATTR_UDN: "mock-unique-id",
}


def get_mock_remote(
    request_error=None,
    authorize_error=None,
    encrypted=False,
    app_id=None,
    encryption_key=None,
    device_info: UndefinedType | None = UNDEFINED,
):
    """Return a mock remote."""
    mock_remote = Mock()

    mock_remote.type = TV_TYPE_ENCRYPTED if encrypted else TV_TYPE_NONENCRYPTED
    mock_remote.app_id = app_id
    mock_remote.enc_key = encryption_key

    def request_pin_code(name=None):
        if request_error is not None:
            raise request_error

    mock_remote.request_pin_code = request_pin_code

    def authorize_pin_code(pincode):
        if pincode == "1234":
            return
        if authorize_error is not None:
            raise authorize_error

    mock_remote.authorize_pin_code = authorize_pin_code

    mock_remote.get_device_info = Mock(
        return_value=MOCK_DEVICE_INFO if device_info is UNDEFINED else device_info
    )

    mock_remote.send_key = Mock()
    mock_remote.get_volume = Mock(return_value=100)

    return mock_remote


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.panasonic_viera.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup
