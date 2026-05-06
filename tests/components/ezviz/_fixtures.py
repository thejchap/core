"""Tryke fixtures for EZVIZ."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture

from homeassistant.components.ezviz import (
    ATTR_TYPE_CAMERA,
    ATTR_TYPE_CLOUD,
    CONF_RFSESSION_ID,
    CONF_SESSION_ID,
    DOMAIN,
)
from homeassistant.const import CONF_PASSWORD, CONF_TYPE, CONF_URL, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.ezviz.async_setup_entry", return_value=True
    ) as setup_entry_mock:
        yield setup_entry_mock


@fixture
def mock_ffmpeg(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Mock ffmpeg is loaded."""
    hass.config.components.add("ffmpeg")


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-username",
        title="test-username",
        data={
            CONF_SESSION_ID: "test-username",
            CONF_RFSESSION_ID: "test-password",
            CONF_URL: "apiieu.ezvizlife.com",
            CONF_TYPE: ATTR_TYPE_CLOUD,
        },
    )


@fixture
def mock_camera_config_entry() -> MockConfigEntry:
    """Return the default mocked camera config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="C666666",
        title="Camera 1",
        data={
            CONF_TYPE: ATTR_TYPE_CAMERA,
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )


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


@fixture
def mock_ezviz_client(
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
) -> Generator[AsyncMock]:
    """Mock the EzvizAPI for easier testing."""
    with (
        patch(
            "homeassistant.components.ezviz.EzvizClient", autospec=True
        ) as mock_ezviz,
        patch(
            "homeassistant.components.ezviz.config_flow.EzvizClient", new=mock_ezviz
        ),
    ):
        instance = mock_ezviz.return_value

        instance.login.return_value = {
            "session_id": "fake_token",
            "rf_session_id": "fake_rf_token",
            "api_url": "apiieu.ezvizlife.com",
        }
        instance.get_detection_sensibility.return_value = True

        yield instance


@fixture
def mock_test_rtsp_auth() -> Generator[MagicMock]:
    """Mock the TestRTSPAuth for easier testing."""
    with patch(
        "homeassistant.components.ezviz.config_flow.TestRTSPAuth"
    ) as mock_ezviz_test_rtsp:
        instance = mock_ezviz_test_rtsp.return_value
        instance.main.return_value = True
        yield instance
