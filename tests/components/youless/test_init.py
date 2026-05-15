"""Test the setup of the Youless integration."""

from tryke import Depends, expect, fixture, test

from homeassistant import setup
from homeassistant.components.youless.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_component

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def async_setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check if the setup of the integration succeeds."""

    entry = await init_component(hass)

    expect(bool(await setup.async_setup_component(hass, DOMAIN, {}))).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(hass.states.async_entity_ids())).to_equal(22)
