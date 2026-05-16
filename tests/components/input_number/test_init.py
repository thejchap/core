"""The tests for the Input number component."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.input_number import (
    ATTR_VALUE,
    DOMAIN,
    SERVICE_DECREMENT,
    SERVICE_INCREMENT,
    SERVICE_RELOAD,
    SERVICE_SET_VALUE,
)
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
)
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockUser, mock_restore_cache
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor() -> int:
    return 0


async def _set_value(hass: HomeAssistant, entity_id: str, value: str) -> None:
    """Set input_number to value."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )


async def _increment(hass: HomeAssistant, entity_id: str) -> None:
    """Increment value of entity."""
    await hass.services.async_call(
        DOMAIN, SERVICE_INCREMENT, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


async def _decrement(hass: HomeAssistant, entity_id: str) -> None:
    """Decrement value of entity."""
    await hass.services.async_call(
        DOMAIN, SERVICE_DECREMENT, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )


@test.cases(
    test.case("none", invalid_config=None),
    test.case("name_with_space", invalid_config={"name with space": None}),
    test.case("min_equals_max", invalid_config={"test_1": {"min": 50, "max": 50}}),
    test.case(
        "initial_outside_range",
        invalid_config={"test_1": {"min": 0, "max": 10, "initial": 11}},
    ),
)
async def config(
    invalid_config: Any,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config."""
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: invalid_config})
    ).to_be(False)


@test
async def set_value(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_value method."""
    expect(
        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test_1": {"initial": 50, "min": 0, "max": 100}}}
        )
    ).to_be(True)
    entity_id = "input_number.test_1"

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(50)

    await _set_value(hass, entity_id, "30.4")

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(30.4)

    await _set_value(hass, entity_id, "70")

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(70)

    async with expect_raises_async(
        vol.Invalid,
        match=r"Invalid value for input_number\.test_1: 110\.0 \(range 0\.0 - 100\.0\)",
    ):
        await _set_value(hass, entity_id, "110")

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(70)


@test
async def increment(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test increment method."""
    expect(
        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test_2": {"initial": 50, "min": 0, "max": 51}}}
        )
    ).to_be(True)
    entity_id = "input_number.test_2"

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(50)

    await _increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(51)

    await _increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(51)


@test
async def rounding(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test increment introducing floating point error is rounded."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {"test_2": {"initial": 2.4, "min": 0, "max": 51, "step": 1.2}}},
        )
    ).to_be(True)
    entity_id = "input_number.test_2"
    expect(2.4 + 1.2 != 3.6).to_be(True)

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(2.4)

    await _increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(3.6)


@test
async def decrement(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test decrement method."""
    expect(
        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test_3": {"initial": 50, "min": 49, "max": 100}}}
        )
    ).to_be(True)
    entity_id = "input_number.test_3"

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(50)

    await _decrement(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(49)

    await _decrement(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(float(state.state)).to_equal(49)


@test
async def mode(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test mode settings."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_default_slider": {"min": 0, "max": 100},
                    "test_explicit_box": {"min": 0, "max": 100, "mode": "box"},
                    "test_explicit_slider": {"min": 0, "max": 100, "mode": "slider"},
                }
            },
        )
    ).to_be(True)

    state = hass.states.get("input_number.test_default_slider")
    expect(state).not_.to_be_none()
    expect(state.attributes["mode"]).to_equal("slider")

    state = hass.states.get("input_number.test_explicit_box")
    expect(state).not_.to_be_none()
    expect(state.attributes["mode"]).to_equal("box")

    state = hass.states.get("input_number.test_explicit_slider")
    expect(state).not_.to_be_none()
    expect(state.attributes["mode"]).to_equal("slider")


@test
async def restore_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass, (State("input_number.b1", "70"), State("input_number.b2", "200"))
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: {"b1": {"min": 0, "max": 100}, "b2": {"min": 10, "max": 100}}},
    )

    state = hass.states.get("input_number.b1")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(70)

    state = hass.states.get("input_number.b2")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(10)


@test
async def restore_invalid_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure an invalid restore state is handled."""
    mock_restore_cache(
        hass, (State("input_number.b1", "="), State("input_number.b2", "200"))
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: {"b1": {"min": 2, "max": 100}, "b2": {"min": 10, "max": 100}}},
    )

    state = hass.states.get("input_number.b1")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(2)

    state = hass.states.get("input_number.b2")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(10)


@test
async def initial_state_overrules_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass, (State("input_number.b1", "70"), State("input_number.b2", "200"))
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "b1": {"initial": 50, "min": 0, "max": 100},
                "b2": {"initial": 60, "min": 0, "max": 100},
            }
        },
    )

    state = hass.states.get("input_number.b1")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(50)

    state = hass.states.get("input_number.b2")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(60)


@test
async def no_initial_state_and_no_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure that entity is create without initial and restore feature."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"b1": {"min": 0, "max": 100}}})

    state = hass.states.get("input_number.b1")
    expect(state).not_.to_be_none()
    expect(float(state.state)).to_equal(0)


@test
async def input_number_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that input_number context works."""
    expect(
        await async_setup_component(
            hass, "input_number", {"input_number": {"b1": {"min": 0, "max": 100}}}
        )
    ).to_be(True)

    state = hass.states.get("input_number.b1")
    expect(state).not_.to_be_none()

    await hass.services.async_call(
        "input_number",
        "increment",
        {"entity_id": state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("input_number.b1")
    expect(state2).not_.to_be_none()
    expect(state.state != state2.state).to_be(True)
    expect(state2.context.user_id).to_equal(hass_admin_user.id)


@test
async def reload(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
    hass_read_only_user: MockUser = Depends(hass_read_only_user_fx),
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {"initial": 50, "min": 0, "max": 51},
                    "test_3": {"initial": 10, "min": 0, "max": 15},
                }
            },
        )
    ).to_be(True)

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_number.test_1")
    state_2 = hass.states.get("input_number.test_2")
    state_3 = hass.states.get("input_number.test_3")

    expect(state_1).not_.to_be_none()
    expect(state_2).to_be_none()
    expect(state_3).not_.to_be_none()
    expect(float(state_1.state)).to_equal(50)
    expect(float(state_3.state)).to_equal(10)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")
    ).not_.to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2")).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")
    ).not_.to_be_none()

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_1": {"initial": 40, "min": 0, "max": 51},
                "test_2": {"initial": 20, "min": 10, "max": 30},
            }
        },
    ):
        async with expect_raises_async(Unauthorized):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_RELOAD,
                blocking=True,
                context=Context(user_id=hass_read_only_user.id),
            )
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
        await hass.async_block_till_done()

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_number.test_1")
    state_2 = hass.states.get("input_number.test_2")
    state_3 = hass.states.get("input_number.test_3")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).to_be_none()
    expect(float(state_1.state)).to_equal(50)
    expect(float(state_2.state)).to_equal(20)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2")
    ).not_.to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")).to_be_none()


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be(True)
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(float(state.state)).to_equal(0)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(
            config={
                DOMAIN: {
                    "from_yaml": {
                        "min": 1,
                        "max": 10,
                        "initial": 5,
                        "step": 1,
                        "mode": "slider",
                    }
                }
            }
        )
    ).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(float(state.state)).to_equal(0)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(float(state.state)).to_equal(5)
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(False)


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(
        await storage_setup(
            config={
                DOMAIN: {
                    "from_yaml": {
                        "min": 1,
                        "max": 10,
                        "initial": 5,
                        "step": 1,
                        "mode": "slider",
                    }
                }
            }
        )
    ).to_be(True)

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    storage_ent = "from_storage"
    yaml_ent = "from_yaml"
    result = {item["id"]: item for item in resp["result"]}

    expect(len(result)).to_equal(1)
    expect(storage_ent in result).to_be(True)
    expect(yaml_ent in result).to_be(False)
    expect(result[storage_ent][ATTR_NAME]).to_equal("from storage")


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test WS delete cleans up entity registry."""
    expect(await storage_setup()).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 6, "type": f"{DOMAIN}/delete", f"{DOMAIN}_id": f"{input_id}"}
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)).to_be_none()


@test
async def update_min_max(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test updating min/max updates the state."""

    settings = {
        "name": "from storage",
        "max": 100,
        "min": 0,
        "step": 1,
        "mode": "slider",
    }
    items = [{"id": "from_storage"} | settings]
    expect(await storage_setup(items)).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).not_.to_be_none()
    expect(state.state).to_be_truthy()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    updated_settings = settings | {"min": 9}
    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal({"id": "from_storage"} | updated_settings)

    state = hass.states.get(input_entity_id)
    expect(float(state.state)).to_equal(9)

    updated_settings = settings | {"max": 5}
    await client.send_json(
        {
            "id": 7,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal({"id": "from_storage"} | updated_settings)

    state = hass.states.get(input_entity_id)
    expect(float(state.state)).to_equal(5)


@test
async def ws_create(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test create WS."""
    expect(await storage_setup(items=[])).to_be(True)

    input_id = "new_input"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)).to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json(
        {
            "id": 6,
            "type": f"{DOMAIN}/create",
            "name": "New Input",
            "max": 20,
            "min": 0,
            "initial": 10,
            "step": 1,
            "mode": "slider",
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(float(state.state)).to_equal(10)


@test
async def setup_no_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test component setup with no config."""
    count_start = len(hass.states.async_entity_ids())
    expect(await async_setup_component(hass, DOMAIN, {})).to_be(True)

    with patch(
        "homeassistant.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )
        await hass.async_block_till_done()

    expect(count_start).to_equal(len(hass.states.async_entity_ids()))
