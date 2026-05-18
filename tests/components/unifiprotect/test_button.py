"""Test the UniFi Protect button platform."""

from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test
from uiprotect.data.devices import Camera, Chime, Doorlock

from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import chime, doorbell, doorlock, ufp
from .utils import (
    MockUFPFixture,
    adopt_devices,
    assert_entity_counts,
    enable_entity,
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
async def button_chime_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    chime: Chime = Depends(chime),
) -> None:
    """Test removing and re-adding a light device."""
    await init_entry(hass, ufp, [chime])
    assert_entity_counts(hass, Platform.BUTTON, 4, 2)
    await remove_entities(hass, ufp, [chime])
    assert_entity_counts(hass, Platform.BUTTON, 0, 0)
    await adopt_devices(hass, ufp, [chime])
    assert_entity_counts(hass, Platform.BUTTON, 4, 2)


@test.cases(
    test.case(
        "reboot",
        unique_id_suffix="reboot",
        entity_id="button.test_chime_restart",
        api_method="reboot_device",
        is_disabled=True,
    ),
    test.case(
        "play",
        unique_id_suffix="play",
        entity_id="button.test_chime_play_chime",
        api_method="play_speaker",
        is_disabled=False,
    ),
)
async def chime_button(
    *,
    unique_id_suffix: str,
    entity_id: str,
    api_method: str,
    is_disabled: bool,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    chime: Chime = Depends(chime),
) -> None:
    """Test chime button entities."""
    await init_entry(hass, ufp, [chime])
    assert_entity_counts(hass, Platform.BUTTON, 4, 2)

    unique_id = f"{chime.mac}_{unique_id_suffix}"

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.disabled).to_be(is_disabled)
    expect(entity.unique_id).to_equal(unique_id)

    if is_disabled:
        await enable_entity(hass, ufp.entry.entry_id, entity_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    with patch.object(ufp.api, api_method, AsyncMock()) as mock_api_method:
        await hass.services.async_call(
            "button", "press", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_api_method.assert_called_once()


@test
async def adopt_button(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test button entity."""
    doorlock._api = ufp.api
    doorlock.is_adopted = False
    doorlock.can_adopt = True

    await init_entry(hass, ufp, [])

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.old_obj = None
    mock_msg.new_obj = doorlock
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    assert_entity_counts(hass, Platform.BUTTON, 1, 1)

    ufp.api.adopt_device = AsyncMock()

    unique_id = f"{doorlock.mac}_adopt"
    entity_id = "button.test_lock_adopt_device"

    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)
    expect(entity.disabled).to_be(False)
    expect(entity.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)

    await hass.services.async_call(
        "button", "press", {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    ufp.api.adopt_device.assert_called_once()


@test
async def adopt_button_removed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    doorbell: Camera = Depends(doorbell),
) -> None:
    """Test button entity."""
    entity_id = "button.test_lock_adopt_device"

    doorlock._api = ufp.api
    doorlock.is_adopted = False
    doorlock.can_adopt = True

    await init_entry(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.BUTTON, 1, 1)
    entity = entity_registry.async_get(entity_id)
    expect(entity).not_.to_be(None)

    await adopt_devices(hass, ufp, [doorlock], fully_adopt=True)
    assert_entity_counts(hass, Platform.BUTTON, 2, 0)
    entity = entity_registry.async_get(entity_id)
    expect(entity).to_be(None)
