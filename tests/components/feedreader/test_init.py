"""The tests for the feedreader component."""

from unittest.mock import patch
import urllib
import urllib.error

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import create_mock_entry
from ._fixtures import feed_one_event
from .const import VALID_CONFIG_DEFAULT

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def setup_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    feed_one_event_data: bytes = Depends(feed_one_event),
) -> None:
    """Test setup error."""
    entry = create_mock_entry(VALID_CONFIG_DEFAULT)
    entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.feedreader.coordinator.feedparser.http.get"
    ) as feedreader:
        feedreader.side_effect = urllib.error.URLError("Test")
        feedreader.return_value = feed_one_event_data
        await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def storage_data_writing() -> None:
    """Stub for test_storage_data_writing."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed() -> None:
    """Stub for test_feed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def atom_feed() -> None:
    """Stub for test_atom_feed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_identical_timestamps() -> None:
    """Stub for test_feed_identical_timestamps."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_with_only_summary() -> None:
    """Stub for test_feed_with_only_summary."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_updates() -> None:
    """Stub for test_feed_updates."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_default_max_length() -> None:
    """Stub for test_feed_default_max_length."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_max_length() -> None:
    """Stub for test_feed_max_length."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_without_publication_date_and_title() -> None:
    """Stub for test_feed_without_publication_date_and_title."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_with_unrecognized_publication_date() -> None:
    """Stub for test_feed_with_unrecognized_publication_date."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_without_items() -> None:
    """Stub for test_feed_without_items."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_invalid_data() -> None:
    """Stub for test_feed_invalid_data."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_parsing_failed() -> None:
    """Stub for test_feed_parsing_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_errors() -> None:
    """Stub for test_feed_errors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def feed_atom_htmlentities() -> None:
    """Stub for test_feed_atom_htmlentities."""

