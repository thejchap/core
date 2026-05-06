"""Tryke fixtures for WLED integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture
from wled import Device as WLEDDevice, Releases

from homeassistant.components.wled.const import DOMAIN
from homeassistant.const import CONF_HOST

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.123"},
        unique_id="aabbccddeeff",
        minor_version=2,
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.wled.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_onboarding() -> Generator[MagicMock]:
    """Mock that Home Assistant is currently onboarding."""
    with patch(
        "homeassistant.components.onboarding.async_is_onboarded",
        return_value=False,
    ) as mock_onboarding:
        yield mock_onboarding


@fixture
def mock_wled_releases() -> Generator[MagicMock]:
    """Return a mocked WLEDReleases client."""
    with patch(
        "homeassistant.components.wled.coordinator.WLEDReleases", autospec=True
    ) as wled_releases_mock:
        wled_releases = wled_releases_mock.return_value
        wled_releases.releases.return_value = Releases(
            beta="1.0.0b5",
            nightly=None,
            repo="wled/WLED",
            stable="0.99.0",
        )

        yield wled_releases


@fixture
def mock_wled(
    _releases: MagicMock = Depends(mock_wled_releases),
) -> Generator[MagicMock]:
    """Return a mocked WLED client."""
    with (
        patch(
            "homeassistant.components.wled.coordinator.WLED", autospec=True
        ) as wled_mock,
        patch("homeassistant.components.wled.config_flow.WLED", new=wled_mock),
    ):
        wled = wled_mock.return_value
        wled.update.return_value = WLEDDevice.from_dict(
            load_json_object_fixture("rgb.json", DOMAIN)
        )
        wled.connected = False
        wled.host = "127.0.0.1"

        yield wled
