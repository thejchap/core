"""The tests for the litejet component."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import scene
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import async_init_integration
from ._fixtures import mock_litejet

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)

ENTITY_SCENE = "scene.litejet_mock_scene_1"
ENTITY_SCENE_NUMBER = 1
ENTITY_OTHER_SCENE = "scene.litejet_mock_scene_2"
ENTITY_OTHER_SCENE_NUMBER = 2


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def disabled_by_default(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_litejet: object = Depends(mock_litejet),
) -> None:
    """Test the scene is disabled by default."""
    await async_init_integration(hass)

    state = hass.states.get(ENTITY_SCENE)
    expect(state is None).to_be(True)

    entry = entity_registry.async_get(ENTITY_SCENE)
    expect(entry is not None).to_be(True)
    expect(entry.disabled).to_be(True)
    expect(entry.disabled_by).to_be(er.RegistryEntryDisabler.INTEGRATION)


@test
async def activate(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: object = Depends(mock_litejet),
) -> None:
    """Test activating the scene."""
    await async_init_integration(hass, use_scene=True)

    state = hass.states.get(ENTITY_SCENE)
    expect(state is not None).to_be(True)

    await hass.services.async_call(
        scene.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SCENE}, blocking=True
    )

    mock_litejet.activate_scene.assert_called_once_with(ENTITY_SCENE_NUMBER)


@test
async def connected_event(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_litejet: object = Depends(mock_litejet),
) -> None:
    """Test handling an event from LiteJet."""
    await async_init_integration(hass, use_scene=True)

    expect(hass.states.get(ENTITY_SCENE).state).to_equal(STATE_UNKNOWN)

    mock_litejet.connected_changed(False, "test")
    await hass.async_block_till_done()

    expect(hass.states.get(ENTITY_SCENE).state).to_equal(STATE_UNAVAILABLE)

    mock_litejet.connected_changed(True, None)
    await hass.async_block_till_done()

    expect(hass.states.get(ENTITY_SCENE).state).to_equal(STATE_UNKNOWN)
