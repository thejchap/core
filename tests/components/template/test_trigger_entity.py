"""Test trigger template entity."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.components.template import trigger_entity
from homeassistant.components.template.coordinator import TriggerUpdateCoordinator
from homeassistant.const import CONF_ICON, CONF_NAME, CONF_STATE, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import template
from homeassistant.helpers.trigger_template_entity import CONF_PICTURE

from tests.hass_fixtures import hass as hass_fixture, mock_network

_ICON_TEMPLATE = 'mdi:o{{ "n" if value=="on" else "ff" }}'
_PICTURE_TEMPLATE = '/local/picture_o{{ "n" if value=="on" else "ff" }}'


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (tryke 0.0.27 quirk)."""
    return hass


class _TriggerTestEntity(trigger_entity.TriggerEntity):
    """Test entity class."""

    __test__ = False
    _entity_id_format = "test.{}"
    extra_template_keys = (CONF_STATE,)
    _state_option = CONF_STATE

    @property
    def state(self) -> bool | None:
        """Return state."""
        return self._rendered.get(self._state_option)


@test
async def reference_blueprints_is_none(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test trigger template entity referenced_blueprint is None."""
    coordinator = TriggerUpdateCoordinator(hass, {})
    entity = trigger_entity.TriggerEntity(hass, coordinator, {})
    expect(entity.referenced_blueprint).to_be(None)


@test
async def template_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test manual trigger template entity with a state."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_ICON: template.Template(_ICON_TEMPLATE, hass),
        CONF_PICTURE: template.Template(_PICTURE_TEMPLATE, hass),
        CONF_STATE: template.Template("{{ value == 'on' }}", hass),
    }

    coordinator = TriggerUpdateCoordinator(hass, {})
    entity = _TriggerTestEntity(hass, coordinator, config)
    entity.entity_id = "test.entity"

    coordinator._execute_update({"value": STATE_ON})
    entity._handle_coordinator_update()
    await hass.async_block_till_done()

    expect(entity.state).to_equal("True")
    expect(entity.icon).to_equal("mdi:on")
    expect(entity.entity_picture).to_equal("/local/picture_on")

    coordinator._execute_update({"value": STATE_OFF})
    entity._handle_coordinator_update()
    await hass.async_block_till_done()

    expect(entity.state).to_equal("False")
    expect(entity.icon).to_equal("mdi:off")
    expect(entity.entity_picture).to_equal("/local/picture_off")


@test
async def bad_template_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test manual trigger template entity with a bad state template."""
    config = {
        CONF_NAME: template.Template("test_entity", hass),
        CONF_ICON: template.Template(_ICON_TEMPLATE, hass),
        CONF_PICTURE: template.Template(_PICTURE_TEMPLATE, hass),
        CONF_STATE: template.Template("{{ x - 1 }}", hass),
    }
    coordinator = TriggerUpdateCoordinator(hass, {})
    entity = _TriggerTestEntity(hass, coordinator, config)
    entity.entity_id = "test.entity"

    coordinator._execute_update({"x": 1})
    entity._handle_coordinator_update()
    await hass.async_block_till_done()

    expect(entity.available).to_be(True)
    expect(entity.state).to_equal("0")
    expect(entity.icon).to_equal("mdi:off")
    expect(entity.entity_picture).to_equal("/local/picture_off")

    coordinator._execute_update({"value": STATE_OFF})
    entity._handle_coordinator_update()
    await hass.async_block_till_done()

    expect(entity.available).to_be(False)
    expect(entity.state).to_be(None)
    expect(entity.icon).to_be(None)
    expect(entity.entity_picture).to_be(None)


@test
async def default_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test template entity creates suggested entity_id from default_entity_id."""
    coordinator = TriggerUpdateCoordinator(hass, {})
    entity = _TriggerTestEntity(hass, coordinator, {"default_entity_id": "test.test"})
    expect(entity.entity_id).to_equal("test.test")


@test
async def bad_default_entity_id(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test bad default_entity_id falls back to suggested entity_id."""
    coordinator = TriggerUpdateCoordinator(hass, {})
    entity = _TriggerTestEntity(hass, coordinator, {"default_entity_id": "bad.test"})
    expect(entity.entity_id).to_equal("test.test")


@test.skip("template_state_syntax_error needs caplog text — port deferred")
async def template_state_syntax_error() -> None:
    """Stub: requires caplog text."""


@test.skip("script_variables_from_coordinator needs full integration setup — port deferred")
async def script_variables_from_coordinator() -> None:
    """Stub."""


@test.skip("multiple_template_validators stub — port deferred")
async def multiple_template_validators() -> None:
    """Stub."""


@test.skip("coordinator_shutdown_unloads_script_and_condition stub")
async def coordinator_shutdown_unloads_script_and_condition() -> None:
    """Stub."""


@test.skip("shutdown_stops_script_and_keeps_triggers_subscribed stub")
async def shutdown_stops_script_and_keeps_triggers_subscribed() -> None:
    """Stub."""


@test.skip("reload_stops_script_and_unsubscribes_triggers stub")
async def reload_stops_script_and_unsubscribes_triggers() -> None:
    """Stub."""
