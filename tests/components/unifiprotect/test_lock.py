"""Test the UniFi Protect lock platform."""

from unittest.mock import AsyncMock, Mock

from tryke import Depends, expect, fixture, test
from uiprotect.data import Doorlock, LockStatusType

from homeassistant.components.lock import LockState
from homeassistant.components.unifiprotect.const import DEFAULT_ATTRIBUTION
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_ENTITY_ID,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import patch_ufp_method
from ._fixtures import doorlock, ufp
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


@fixture
def unadopted_doorlock(doorlock: Doorlock = Depends(doorlock)) -> Doorlock:
    """Mock UniFi Protect Doorlock device (unadopted)."""
    no_doorlock = doorlock.model_copy()
    no_doorlock.name = "Unadopted Lock"
    no_doorlock.is_adopted = False
    return no_doorlock


@test
async def lock_remove(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
) -> None:
    """Test removing and re-adding a lock device."""
    await init_entry(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)
    await remove_entities(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.LOCK, 0, 0)
    await adopt_devices(hass, ufp, [doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)


@test
async def lock_setup(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity setup."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    unique_id = f"{doorlock.mac}_lock"
    entity_id = "lock.test_lock_lock"

    entry = entity_registry.async_get(entity_id)
    expect(entry).not_.to_be(None)
    expect(entry.unique_id).to_equal(unique_id)

    state = hass.states.get(entity_id)
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(LockState.UNLOCKED)
    expect(state.attributes[ATTR_ATTRIBUTION]).to_equal(DEFAULT_ATTRIBUTION)


@test
async def lock_locked(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity locked."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    new_lock = doorlock.model_copy()
    new_lock.lock_status = LockStatusType.CLOSED

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_lock

    ufp.api.bootstrap.doorlocks = {new_lock.id: new_lock}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("lock.test_lock_lock")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(LockState.LOCKED)


@test
async def lock_unlocking(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity unlocking."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    new_lock = doorlock.model_copy()
    new_lock.lock_status = LockStatusType.OPENING

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_lock

    ufp.api.bootstrap.doorlocks = {new_lock.id: new_lock}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("lock.test_lock_lock")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(LockState.UNLOCKING)


@test
async def lock_locking(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity locking."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    new_lock = doorlock.model_copy()
    new_lock.lock_status = LockStatusType.CLOSING

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_lock

    ufp.api.bootstrap.doorlocks = {new_lock.id: new_lock}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("lock.test_lock_lock")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(LockState.LOCKING)


@test
async def lock_jammed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity jammed."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    new_lock = doorlock.model_copy()
    new_lock.lock_status = LockStatusType.JAMMED_WHILE_CLOSING

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_lock

    ufp.api.bootstrap.doorlocks = {new_lock.id: new_lock}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("lock.test_lock_lock")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(LockState.JAMMED)


@test
async def lock_unavailable(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity unavailable."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    new_lock = doorlock.model_copy()
    new_lock.lock_status = LockStatusType.NOT_CALIBRATED

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_lock

    ufp.api.bootstrap.doorlocks = {new_lock.id: new_lock}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    state = hass.states.get("lock.test_lock_lock")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_UNAVAILABLE)


@test
async def lock_do_lock(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity lock service."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    with patch_ufp_method(
        doorlock, "close_lock", new_callable=AsyncMock
    ) as mock_method:
        await hass.services.async_call(
            "lock",
            "lock",
            {ATTR_ENTITY_ID: "lock.test_lock_lock"},
            blocking=True,
        )

        mock_method.assert_called_once()


@test
async def lock_do_unlock(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ufp: MockUFPFixture = Depends(ufp),
    doorlock: Doorlock = Depends(doorlock),
    unadopted_doorlock: Doorlock = Depends(unadopted_doorlock),
) -> None:
    """Test lock entity unlock service."""
    await init_entry(hass, ufp, [doorlock, unadopted_doorlock])
    assert_entity_counts(hass, Platform.LOCK, 1, 1)

    new_lock = doorlock.model_copy()
    new_lock.lock_status = LockStatusType.CLOSED

    mock_msg = Mock()
    mock_msg.changed_data = {}
    mock_msg.new_obj = new_lock

    ufp.api.bootstrap.doorlocks = {new_lock.id: new_lock}
    ufp.ws_msg(mock_msg)
    await hass.async_block_till_done()

    with patch_ufp_method(new_lock, "open_lock", new_callable=AsyncMock) as mock_method:
        await hass.services.async_call(
            "lock",
            "unlock",
            {ATTR_ENTITY_ID: "lock.test_lock_lock"},
            blocking=True,
        )

        mock_method.assert_called_once()
