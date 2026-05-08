"""Test LastFM component setup process."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.lastfm.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import MockUser
from ._fixtures import (
    ComponentSetup,
    config_entry,
    default_user,
    setup_integration,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    setup: ComponentSetup = Depends(setup_integration),
    cfg_entry: MockConfigEntry = Depends(config_entry),
    user: MockUser = Depends(default_user),
) -> None:
    """Test load and unload entry."""
    await setup(cfg_entry, user)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    state = hass.states.get("sensor.lastfm_testaccount1")
    expect(state is not None).to_be(True)

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.lastfm_testaccount1")
    expect(state is None).to_be(True)
