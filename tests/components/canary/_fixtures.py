"""Tryke fixtures for Canary."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from canary.api import Api
from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass


@fixture
def mock_ffmpeg(hass: HomeAssistant = Depends(hass)) -> None:
    """Mock ffmpeg is loaded."""
    hass.config.components.add("ffmpeg")


@fixture
def canary() -> Generator[MagicMock]:
    """Mock the CanaryApi for easier testing."""
    with (
        patch.object(Api, "login", return_value=True),
        patch("homeassistant.components.canary.Api") as mock_canary,
    ):
        instance = mock_canary.return_value = Api(
            "test-username",
            "test-password",
            1,
        )

        instance.login = MagicMock(return_value=True)
        instance.get_entries = MagicMock(return_value=[])
        instance.get_locations = MagicMock(return_value=[])
        instance.get_location = MagicMock(return_value=None)
        instance.get_modes = MagicMock(return_value=[])
        instance.get_readings = MagicMock(return_value=[])
        instance.get_latest_readings = MagicMock(return_value=[])
        instance.set_location_mode = MagicMock(return_value=None)

        yield mock_canary


@fixture
def canary_config_flow() -> Generator[MagicMock]:
    """Mock the CanaryApi for easier config flow testing."""
    with (
        patch.object(Api, "login", return_value=True),
        patch("homeassistant.components.canary.config_flow.Api") as mock_canary,
    ):
        instance = mock_canary.return_value = Api(
            "test-username",
            "test-password",
            1,
        )

        instance.login = MagicMock(return_value=True)
        instance.get_entries = MagicMock(return_value=[])
        instance.get_locations = MagicMock(return_value=[])
        instance.get_location = MagicMock(return_value=None)
        instance.get_modes = MagicMock(return_value=[])
        instance.get_readings = MagicMock(return_value=[])
        instance.get_latest_readings = MagicMock(return_value=[])
        instance.set_location_mode = MagicMock(return_value=None)

        yield mock_canary


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
