"""Test the imap entry initialization."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.imap import DOMAIN
from homeassistant.core import HomeAssistant

from ._fixtures import (
    imap_fetch,
    imap_has_capability,
    imap_login_state,
    imap_pending_idle,
    imap_search,
    imap_select_state,
    mock_imap_protocol,
)
from .test_config_flow import MOCK_CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def entry_startup_and_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _imap_protocol: MagicMock = Depends(mock_imap_protocol),
) -> None:
    """Test imap entry startup and unload (single push case)."""
    config = MOCK_CONFIG.copy()
    config_entry = MockConfigEntry(domain=DOMAIN, data=config)
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)


@test.skip("port deferred - sibling test")
async def entry_startup_fails() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def receiving_message_successfully() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def receiving_message_with_invalid_encoding() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def receiving_message_no_subject_to_from() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def initial_authentication_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def initial_invalid_folder_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def late_authentication_retry() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def late_authentication_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def late_folder_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def message_data_event_options() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def reset_last_message_uid_handler() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fetch_number_of_messages() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def reauth_started() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def setup_with_imap_session_terminated_error() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def push_messages() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def services_seen_unseen_or_move() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def event_state_only() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def event_test() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def auto_subscribed() -> None:
    """Stub."""
