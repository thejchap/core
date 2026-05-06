"""Tryke fixtures for Transmission tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from transmission_rpc.session import Session, SessionStats
from tryke import fixture

from homeassistant.components.transmission.const import DOMAIN

from . import MOCK_CONFIG_DATA

from tests.common import MockConfigEntry


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.transmission.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Transmission",
        data=MOCK_CONFIG_DATA,
        entry_id="01J0BC4QM2YBRP6H5G933AETT7",
    )


@fixture
def mock_transmission_client() -> Generator[AsyncMock]:
    """Mock a Transmission client."""
    with patch(
        "homeassistant.components.transmission.transmission_rpc.Client",
        autospec=False,
    ) as mock_client_class:
        client = mock_client_class.return_value

        client.server_version = "4.0.5 (a6fe2a64aa)"

        session_stats_data = {
            "uploadSpeed": 1,
            "downloadSpeed": 1,
            "activeTorrentCount": 0,
            "pausedTorrentCount": 0,
            "torrentCount": 0,
            "current-stats": {
                "uploadedBytes": 5368709120,
                "downloadedBytes": 10737418240,
            },
            "cumulative-stats": {
                "uploadedBytes": 85899345920,
                "downloadedBytes": 107374182400,
            },
        }
        client.session_stats.return_value = SessionStats(fields=session_stats_data)

        session_data = {"alt-speed-enabled": False}
        client.get_session.return_value = Session(fields=session_data)

        client.get_torrents.return_value = []

        yield mock_client_class


@fixture
def patch_sleep() -> Generator[None]:
    """Fixture to remove sleep in tests."""
    with patch("homeassistant.components.transmission.switch.AFTER_WRITE_SLEEP", 0):
        yield
