"""The tests for the lock component."""

from __future__ import annotations

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.lock import (
    ATTR_CODE,
    CONF_DEFAULT_CODE,
    DOMAIN,
    SERVICE_LOCK,
    SERVICE_OPEN,
    SERVICE_UNLOCK,
    LockEntityFeature,
    LockState,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import UNDEFINED, UndefinedType

from ._fixtures import setup_mock_lock

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


async def help_test_async_lock_service(
    hass: HomeAssistant,
    entity_id: str,
    service: str,
    code: str | None | UndefinedType = UNDEFINED,
) -> None:
    """Help to lock a test lock."""
    data: dict[str, Any] = {"entity_id": entity_id}
    if code is not UNDEFINED:
        data[ATTR_CODE] = code

    await hass.services.async_call(DOMAIN, service, data, blocking=True)


@test
async def lock_default(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock entity with defaults."""
    mock_lock_entity = await setup_mock_lock(hass)

    expect(mock_lock_entity.code_format).to_be_none()
    expect(mock_lock_entity.state).to_be_none()
    expect(mock_lock_entity.is_jammed).to_be_none()
    expect(mock_lock_entity.is_locked).to_be_none()
    expect(mock_lock_entity.is_locking).to_be_none()
    expect(mock_lock_entity.is_unlocking).to_be_none()
    expect(mock_lock_entity.is_opening).to_be_none()
    expect(mock_lock_entity.is_open).to_be_none()


@test
async def lock_states(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock entity states."""
    mock_lock_entity = await setup_mock_lock(hass)

    expect(mock_lock_entity.state).to_be_none()

    mock_lock_entity._attr_is_locking = True
    expect(bool(mock_lock_entity.is_locking)).to_be(True)
    expect(mock_lock_entity.state).to_equal(LockState.LOCKING)

    mock_lock_entity._attr_is_locked = True
    mock_lock_entity._attr_is_locking = False
    expect(bool(mock_lock_entity.is_locked)).to_be(True)
    expect(mock_lock_entity.state).to_equal(LockState.LOCKED)

    mock_lock_entity._attr_is_unlocking = True
    expect(bool(mock_lock_entity.is_unlocking)).to_be(True)
    expect(mock_lock_entity.state).to_equal(LockState.UNLOCKING)

    mock_lock_entity._attr_is_locked = False
    mock_lock_entity._attr_is_unlocking = False
    expect(bool(mock_lock_entity.is_locked)).to_be(False)
    expect(mock_lock_entity.state).to_equal(LockState.UNLOCKED)

    mock_lock_entity._attr_is_jammed = True
    expect(bool(mock_lock_entity.is_jammed)).to_be(True)
    expect(mock_lock_entity.state).to_equal(LockState.JAMMED)
    expect(bool(mock_lock_entity.is_locked)).to_be(False)

    mock_lock_entity._attr_is_jammed = False
    mock_lock_entity._attr_is_opening = True
    expect(bool(mock_lock_entity.is_opening)).to_be(True)
    expect(mock_lock_entity.state).to_equal(LockState.OPENING)
    expect(bool(mock_lock_entity.is_opening)).to_be(True)

    mock_lock_entity._attr_is_opening = False
    mock_lock_entity._attr_is_open = True
    expect(bool(mock_lock_entity.is_opening)).to_be(False)
    expect(mock_lock_entity.state).to_equal(LockState.OPEN)
    expect(bool(mock_lock_entity.is_opening)).to_be(False)
    expect(bool(mock_lock_entity.is_open)).to_be(True)


@test
async def set_mock_lock_options(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test mock attributes and default code stored in the registry."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )

    entity_registry.async_update_entity_options(
        "lock.test_lock", "lock", {CONF_DEFAULT_CODE: "1234"}
    )
    await hass.async_block_till_done()

    expect(mock_lock_entity._lock_option_default_code).to_equal("1234")
    state = hass.states.get(mock_lock_entity.entity_id)
    expect(state is not None).to_be(True)
    expect(state.attributes["code_format"]).to_equal(r"^\d{4}$")
    expect(state.attributes["supported_features"]).to_equal(LockEntityFeature.OPEN)


@test
async def default_code_option_update(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test default code stored in the registry is updated."""
    mock_lock_entity = await setup_mock_lock(hass, code_format=r"^\d{4}$")

    expect(mock_lock_entity._lock_option_default_code).to_equal("")

    entity_registry.async_update_entity_options(
        "lock.test_lock", "lock", {CONF_DEFAULT_CODE: "4321"}
    )
    await hass.async_block_till_done()

    expect(mock_lock_entity._lock_option_default_code).to_equal("4321")


@test
async def lock_open_with_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock entity with open service."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )
    state = hass.states.get(mock_lock_entity.entity_id)
    expect(state.attributes["code_format"]).to_equal(r"^\d{4}$")

    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_OPEN
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_OPEN, code=""
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_OPEN, code="HELLO"
        )
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_OPEN, code="1234"
    )
    expect(mock_lock_entity.calls_open.call_count).to_equal(1)
    mock_lock_entity.calls_open.assert_called_with(code="1234")


@test
async def lock_lock_with_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock entity with open service."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )
    state = hass.states.get(mock_lock_entity.entity_id)
    expect(state.attributes["code_format"]).to_equal(r"^\d{4}$")

    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code="1234"
    )
    mock_lock_entity.calls_unlock.assert_called_with(code="1234")
    expect(mock_lock_entity.calls_lock.call_count).to_equal(0)

    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_LOCK
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_LOCK, code=""
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_LOCK, code="HELLO"
        )
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_LOCK, code="1234"
    )
    expect(mock_lock_entity.calls_lock.call_count).to_equal(1)
    mock_lock_entity.calls_lock.assert_called_with(code="1234")


@test
async def lock_unlock_with_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test unlock entity with open service."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )
    state = hass.states.get(mock_lock_entity.entity_id)
    expect(state.attributes["code_format"]).to_equal(r"^\d{4}$")

    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_LOCK, code="1234"
    )
    mock_lock_entity.calls_lock.assert_called_with(code="1234")
    expect(mock_lock_entity.calls_unlock.call_count).to_equal(0)

    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_UNLOCK
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code=""
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code="HELLO"
        )
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code="1234"
    )
    expect(mock_lock_entity.calls_unlock.call_count).to_equal(1)
    mock_lock_entity.calls_unlock.assert_called_with(code="1234")


@test
async def lock_with_illegal_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock entity with default code that does not match the code format."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )

    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_OPEN, code="123456"
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_LOCK, code="123456"
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code="123456"
        )


@test
async def lock_with_no_code(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test lock entity without code."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=None,
        supported_features=LockEntityFeature.OPEN,
    )

    await help_test_async_lock_service(hass, mock_lock_entity.entity_id, SERVICE_OPEN)
    mock_lock_entity.calls_open.assert_called_with()
    await help_test_async_lock_service(hass, mock_lock_entity.entity_id, SERVICE_LOCK)
    mock_lock_entity.calls_lock.assert_called_with()
    await help_test_async_lock_service(hass, mock_lock_entity.entity_id, SERVICE_UNLOCK)
    mock_lock_entity.calls_unlock.assert_called_with()

    mock_lock_entity.calls_open.reset_mock()
    mock_lock_entity.calls_lock.reset_mock()
    mock_lock_entity.calls_unlock.reset_mock()

    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_OPEN, code=""
    )
    mock_lock_entity.calls_open.assert_called_with()
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_LOCK, code=""
    )
    mock_lock_entity.calls_lock.assert_called_with()
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code=""
    )
    mock_lock_entity.calls_unlock.assert_called_with()


@test
async def lock_with_default_code(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test lock entity with default code."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )

    entity_registry.async_update_entity_options(
        "lock.test_lock", "lock", {CONF_DEFAULT_CODE: "1234"}
    )
    await hass.async_block_till_done()

    expect(mock_lock_entity.state_attributes).to_equal({"code_format": r"^\d{4}$"})
    expect(mock_lock_entity._lock_option_default_code).to_equal("1234")

    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_OPEN, code="1234"
    )
    mock_lock_entity.calls_open.assert_called_with(code="1234")
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_LOCK, code="1234"
    )
    mock_lock_entity.calls_lock.assert_called_with(code="1234")
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code="1234"
    )
    mock_lock_entity.calls_unlock.assert_called_with(code="1234")

    mock_lock_entity.calls_open.reset_mock()
    mock_lock_entity.calls_lock.reset_mock()
    mock_lock_entity.calls_unlock.reset_mock()

    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_OPEN, code=""
    )
    mock_lock_entity.calls_open.assert_called_with(code="1234")
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_LOCK, code=""
    )
    mock_lock_entity.calls_lock.assert_called_with(code="1234")
    await help_test_async_lock_service(
        hass, mock_lock_entity.entity_id, SERVICE_UNLOCK, code=""
    )
    mock_lock_entity.calls_unlock.assert_called_with(code="1234")


@test
async def lock_with_illegal_default_code(
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test lock entity with illegal default code."""
    mock_lock_entity = await setup_mock_lock(
        hass,
        code_format=r"^\d{4}$",
        supported_features=LockEntityFeature.OPEN,
    )

    entity_registry.async_update_entity_options(
        "lock.test_lock", "lock", {CONF_DEFAULT_CODE: "123456"}
    )
    await hass.async_block_till_done()

    expect(mock_lock_entity.state_attributes).to_equal({"code_format": r"^\d{4}$"})
    expect(mock_lock_entity._lock_option_default_code).to_equal("")

    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_OPEN
        )
    async with expect_raises_async(ServiceValidationError):
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_LOCK
        )

    # The translated message check from the original test relies on
    # `tests/components/conftest.py` patching `async_call` to lazily load
    # exception translations. Tryke does not install that wrapper, so here
    # we only assert the raised exception's `translation_key`, which the
    # original assertion ultimately probes.
    raised: ServiceValidationError | None = None
    try:
        await help_test_async_lock_service(
            hass, mock_lock_entity.entity_id, SERVICE_UNLOCK
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised is not None).to_be(True)
    expect(raised.translation_key).to_equal("add_default_code")
    expect(raised.translation_domain).to_equal("lock")
    expect(raised.translation_placeholders).to_equal(
        {"entity_id": "lock.test_lock", "code_format": r"^\d{4}$"}
    )


