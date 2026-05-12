"""Test the ekey bionyx event platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.event import ATTR_EVENT_TYPES
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


async def _load_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@test
async def event_entity_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test event entity is set up correctly."""
    await _load_entry(hass, entry)
    state = hass.states.get(f"event.{entry.data['webhooks'][0]['name']}")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def event_types_attribute(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test event entity has correct event_types attribute."""
    await _load_entry(hass, entry)
    state = hass.states.get(f"event.{entry.data['webhooks'][0]['name']}")
    expect(state).not_.to_be(None)
    event_types = state.attributes.get(ATTR_EVENT_TYPES)
    expect(event_types).to_equal(["event happened"])


@test
async def config_entry_unload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
) -> None:
    """Test config entry can be unloaded."""
    await _load_entry(hass, entry)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    state = hass.states.get(f"event.{entry.data['webhooks'][0]['name']}")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNKNOWN)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)
    state = hass.states.get(f"event.{entry.data['webhooks'][0]['name']}")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test.skip("webhook_test_env requires hass_client_no_auth — port deferred")
async def webhook_handler_triggers_event() -> None:
    """Stub for test_webhook_handler_triggers_event."""


@test.skip("webhook_test_env requires hass_client_no_auth — port deferred")
async def webhook_handler_rejects_invalid_auth() -> None:
    """Stub for test_webhook_handler_rejects_invalid_auth."""


@test.skip("webhook_test_env requires hass_client_no_auth — port deferred")
async def webhook_handler_missing_auth() -> None:
    """Stub for test_webhook_handler_missing_auth."""


@test.skip("webhook_test_env requires hass_client_no_auth — port deferred")
async def webhook_handler_invalid_json() -> None:
    """Stub for test_webhook_handler_invalid_json."""


# silence unused-import lint for fixture used only via Depends
_ = config_entry
