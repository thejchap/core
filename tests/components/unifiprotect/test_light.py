"""Test the UniFi Protect light platform."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import Light
from uiprotect.data.types import LEDLevel

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import light, ufp, unadopted_light
from .utils import (
    MockUFPFixture,
    adopt_devices,
    assert_entity_counts,
    init_entry,
    remove_entities,
)

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Force a HookExecutor for this module (tryke discovery quirk)."""
    return 0


@test
async def light_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
) -> None:
    """Test removing and re-adding a light device."""
    await init_entry(hass, ufp, [light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)
    await remove_entities(hass, ufp, [light])
    assert_entity_counts(hass, Platform.LIGHT, 0, 0)
    await adopt_devices(hass, ufp, [light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)


@test
async def light_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
    unadopted_light: Light = Depends(unadopted_light),
) -> None:
    """Test light entity setup."""
    await init_entry(hass, ufp, [light, unadopted_light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)

    unique_id = light.mac
    entity_id = "light.test_light"

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def light_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
    unadopted_light: Light = Depends(unadopted_light),
) -> None:
    """Test light entity update."""
    await init_entry(hass, ufp, [light, unadopted_light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)

    new_light = light.model_copy()
    new_light.is_light_on = True
    new_light.light_device_settings.led_level = LEDLevel(3)

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_light

    ufp.api.bootstrap.lights = {new_light.id: new_light}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("light.test_light")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_BRIGHTNESS]).to_equal(128)


@test
async def light_turn_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
    unadopted_light: Light = Depends(unadopted_light),
) -> None:
    """Test light entity turn on."""
    light._api = ufp.api
    light.api.update_light_public = AsyncMock()

    await init_entry(hass, ufp, [light, unadopted_light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)

    entity_id = "light.test_light"
    await hass.services.async_call(
        "light", "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    expect(light.api.update_light_public.called).to_be(True)
    light.api.update_light_public.assert_called_once_with(
        light.id, is_light_force_enabled=True, light_device_settings=None
    )


@test
async def light_turn_on_with_brightness(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
    unadopted_light: Light = Depends(unadopted_light),
) -> None:
    """Test light entity turn on with brightness."""
    light._api = ufp.api
    light.api.update_light_public = AsyncMock()

    await init_entry(hass, ufp, [light, unadopted_light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)

    entity_id = "light.test_light"
    await hass.services.async_call(
        "light",
        "turn_on",
        {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 128},
        blocking=True,
    )

    expect(light.api.update_light_public.called).to_be(True)
    call_kwargs = light.api.update_light_public.call_args[1]
    expect(call_kwargs["is_light_force_enabled"]).to_be(True)
    expect(call_kwargs["light_device_settings"]).not_.to_be(None)
    expect(call_kwargs["light_device_settings"].led_level).to_equal(3)


@test
async def light_turn_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    light: Light = Depends(light),
    unadopted_light: Light = Depends(unadopted_light),
) -> None:
    """Test light entity turn off."""
    light._api = ufp.api
    light.api.update_light_public = AsyncMock()

    await init_entry(hass, ufp, [light, unadopted_light])
    assert_entity_counts(hass, Platform.LIGHT, 1, 1)

    entity_id = "light.test_light"
    await hass.services.async_call(
        "light", "turn_off", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    expect(light.api.update_light_public.called).to_be(True)
    light.api.update_light_public.assert_called_once_with(
        light.id, is_light_force_enabled=False
    )
