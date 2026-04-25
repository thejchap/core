"""Tryke fixtures for Tuya tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture

from homeassistant.components.tuya.const import (
    CONF_ENDPOINT,
    CONF_TERMINAL_ID,
    CONF_TOKEN_INFO,
    CONF_USER_CODE,
    DOMAIN,
)

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        title="Test Tuya entry",
        domain=DOMAIN,
        data={
            CONF_ENDPOINT: "test_endpoint",
            CONF_TERMINAL_ID: "test_terminal",
            CONF_TOKEN_INFO: "test_token",
            CONF_USER_CODE: "test_user_code",
        },
        unique_id="12345",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.tuya.async_setup_entry", return_value=True):
        yield


@fixture
def mock_tuya_login_control() -> Generator[MagicMock]:
    """Return a mocked Tuya login control."""
    with patch(
        "homeassistant.components.tuya.config_flow.LoginControl", autospec=True
    ) as login_control_mock:
        login_control = login_control_mock.return_value
        login_control.qr_code.return_value = {
            "success": True,
            "result": {
                "qrcode": "mocked_qr_code",
            },
        }
        login_control.login_result.return_value = (
            True,
            {
                "t": "mocked_t",
                "uid": "mocked_uid",
                "username": "mocked_username",
                "expire_time": "mocked_expire_time",
                "access_token": "mocked_access_token",
                "refresh_token": "mocked_refresh_token",
                "terminal_id": "mocked_terminal_id",
                "endpoint": "mocked_endpoint",
            },
        )
        yield login_control
