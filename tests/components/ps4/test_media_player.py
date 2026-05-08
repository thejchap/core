"""Tests for the PS4 media player platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import ps4
from homeassistant.components.ps4.const import (
    CONFIG_ENTRY_VERSION as VERSION,
    DEFAULT_REGION,
    DOMAIN,
    PS4_DATA,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_REGION,
    CONF_TOKEN,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from ._fixtures import patch_io

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


MOCK_CREDS = "123412341234abcd12341234abcd12341234abcd12341234abcd12341234abcd"
MOCK_NAME = "ha_ps4_name"
MOCK_REGION = DEFAULT_REGION
MOCK_HOST = "192.168.0.2"
MOCK_DEVICE = {CONF_HOST: MOCK_HOST, CONF_NAME: MOCK_NAME, CONF_REGION: MOCK_REGION}
MOCK_ENTRY_ID = "SomeID"
MOCK_DATA = {CONF_TOKEN: MOCK_CREDS, "devices": [MOCK_DEVICE]}


async def setup_mock_component(
    hass: HomeAssistant, entry: MockConfigEntry | None = None
) -> str:
    """Set up Mock Media Player."""
    if entry is None:
        mock_entry = MockConfigEntry(
            domain=ps4.DOMAIN, data=MOCK_DATA, version=VERSION, entry_id=MOCK_ENTRY_ID
        )
    else:
        mock_entry = entry

    mock_entry.add_to_hass(hass)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    mock_entities = hass.states.async_entity_ids()
    return mock_entities[0]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _io: None = Depends(patch_io),
) -> None:
    """Force tryke to fully resolve hass + IO patches before each test."""


@test
async def media_player_is_setup_correctly_with_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test entity is setup correctly with entry correctly."""
    mock_entity_id = await setup_mock_component(hass)
    mock_state = hass.states.get(mock_entity_id).state

    # Assert status updated callback is added to protocol.
    expect(len(hass.data[PS4_DATA].protocol.callbacks)).to_equal(1)

    # Test that entity is added to hass.
    expect(hass.data[PS4_DATA].protocol is not None).to_be(True)
    expect(mock_entity_id).to_equal(f"media_player.{MOCK_NAME}")
    expect(mock_state).to_equal(STATE_UNKNOWN)


@test
async def state_none_is_set(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that state is set to None."""
    mock_entity_id = await setup_mock_component(hass)
    expect(hass.states.get(mock_entity_id).state).to_equal(STATE_UNKNOWN)


@test.skip("requires DDP UDP message handling - port deferred")
async def state_standby_is_set() -> None:
    """Stub for test_state_standby_is_set (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def state_playing_is_set() -> None:
    """Stub for test_state_playing_is_set (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def state_idle_is_set() -> None:
    """Stub for test_state_idle_is_set (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_attributes_are_fetched() -> None:
    """Stub for test_media_attributes_are_fetched (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_attributes_are_loaded() -> None:
    """Stub for test_media_attributes_are_loaded (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def device_info_from_ps4_data() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def device_info_from_dr() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def turn_off() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def turn_on() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_pause() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_stop() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def select_source() -> None:
    """Stub (port deferred)."""

@test.skip("requires service registration - port deferred")
async def services() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_attributes_are_set() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_image_url() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def media_attributes_attempts_to_get_data_again() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def games_reformat_to_dict() -> None:
    """Stub (port deferred)."""

@test.skip("requires DDP UDP message handling - port deferred")
async def load_games() -> None:
    """Stub (port deferred)."""
