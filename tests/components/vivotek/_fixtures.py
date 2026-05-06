"""Tryke fixtures for Vivotek tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.vivotek import CONF_SECURITY_LEVEL
from homeassistant.components.vivotek.const import (
    CONF_FRAMERATE,
    CONF_STREAM_PATH,
    DOMAIN,
)
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_IP_ADDRESS,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
)

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.vivotek.async_setup_entry", return_value=True):
        yield


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock existing config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_PORT: 80,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "pass1234",
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_SSL: False,
            CONF_VERIFY_SSL: True,
            CONF_SECURITY_LEVEL: "admin",
            CONF_STREAM_PATH: "/live.sdp",
        },
        options={CONF_FRAMERATE: 2},
        title="Vivotek Camera",
        unique_id="11:22:33:44:55:66",
    )


@fixture
def mock_vivotek_camera() -> Generator[AsyncMock]:
    """Mock the VivotekCamera client."""
    with patch(
        "homeassistant.components.vivotek.VivotekCamera", autospec=True
    ) as vivotek_camera:
        instance = vivotek_camera.return_value
        instance.get_mac.return_value = "11:22:33:44:55:66"
        yield instance
