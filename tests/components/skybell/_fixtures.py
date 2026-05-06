"""Tryke fixtures for Skybell tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from aioskybell import Skybell, SkybellDevice
from tryke import fixture

USERNAME = "user"
PASSWORD = "password"
USER_ID = "1234567890abcdef12345678"

CONF_DATA = {
    "email": USERNAME,
    "password": PASSWORD,
}


@fixture
def skybell_mock() -> Generator[AsyncMock]:
    """Fixture for our skybell tests."""
    mocked_skybell_device = AsyncMock(spec=SkybellDevice)

    mocked_skybell = AsyncMock(spec=Skybell)
    mocked_skybell.async_get_devices.return_value = [mocked_skybell_device]
    mocked_skybell.async_send_request.return_value = {"id": USER_ID}
    mocked_skybell.user_id = USER_ID

    with (
        patch(
            "homeassistant.components.skybell.config_flow.Skybell",
            return_value=mocked_skybell,
        ),
        patch("homeassistant.components.skybell.Skybell", return_value=mocked_skybell),
    ):
        yield mocked_skybell


@fixture
def setup_entry() -> Generator[None]:
    """Make sure component doesn't initialize."""
    with patch(
        "homeassistant.components.skybell.async_setup_entry",
        return_value=True,
    ):
        yield
