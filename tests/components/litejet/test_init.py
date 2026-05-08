"""The tests for the litejet component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import litejet
from homeassistant.components.litejet.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import async_init_integration
from ._fixtures import mock_litejet

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def setup_with_no_config(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that nothing happens."""
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)
    expect(DOMAIN in hass.data).to_be(False)


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: object = Depends(mock_litejet),
) -> None:
    """Test being able to unload an entry."""
    entry = await async_init_integration(hass, use_switch=True, use_scene=True)

    expect(await litejet.async_unload_entry(hass, entry)).to_be(True)
    expect(DOMAIN in hass.data).to_be(False)
