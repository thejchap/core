"""The tests for the counter component."""

from collections.abc import Callable, Coroutine
import logging
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.counter import (
    ATTR_EDITABLE,
    ATTR_INITIAL,
    ATTR_MAXIMUM,
    ATTR_MINIMUM,
    ATTR_STEP,
    CONF_ICON,
    CONF_INITIAL,
    CONF_MAXIMUM,
    CONF_MINIMUM,
    CONF_NAME,
    CONF_RESTORE,
    CONF_STEP,
    DEFAULT_INITIAL,
    DEFAULT_STEP,
    DOMAIN,
    SERVICE_SET_VALUE,
    VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME, ATTR_ICON, ATTR_NAME
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import storage_setup as storage_setup_fx
from .common import async_decrement, async_increment, async_reset

from tests.common import MockUser, mock_restore_cache
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_ws_client as hass_ws_client_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor() -> int:
    return 0


@test.cases(
    test.case("none", invalid_config=None),
    test.case("int", invalid_config=1),
    test.case("name_with_space", invalid_config={"name with space": None}),
)
async def config(
    invalid_config: Any,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config."""
    expect(
        not await async_setup_component(hass, DOMAIN, {DOMAIN: invalid_config})
    ).to_be(True)


@test
async def config_options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    config = {
        DOMAIN: {
            "test_1": {},
            "test_2": {
                CONF_NAME: "Hello World",
                CONF_ICON: "mdi:work",
                CONF_INITIAL: 10,
                CONF_RESTORE: False,
                CONF_STEP: 5,
            },
            "test_3": None,
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()
    await hass.async_block_till_done()

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    expect(count_start + 3 == len(hass.states.async_entity_ids())).to_be(True)
    await hass.async_block_till_done()

    state_1 = hass.states.get("counter.test_1")
    state_2 = hass.states.get("counter.test_2")
    state_3 = hass.states.get("counter.test_3")

    expect(state_1).to_be_truthy()
    expect(state_2).to_be_truthy()
    expect(state_3).to_be_truthy()

    expect(int(state_1.state)).to_equal(0)
    expect(ATTR_ICON not in state_1.attributes).to_be(True)
    expect(ATTR_FRIENDLY_NAME not in state_1.attributes).to_be(True)

    expect(int(state_2.state)).to_equal(10)
    expect(state_2.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Hello World")
    expect(state_2.attributes.get(ATTR_ICON)).to_equal("mdi:work")

    expect(state_3.attributes.get(ATTR_INITIAL)).to_equal(DEFAULT_INITIAL)
    expect(state_3.attributes.get(ATTR_STEP)).to_equal(DEFAULT_STEP)


@test
async def methods(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test increment, decrement, set value, and reset methods."""
    config = {DOMAIN: {"test_1": {}}}

    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()

    entity_id = "counter.test_1"

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(0)

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(1)

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(2)

    async_decrement(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(1)

    async_reset(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(0)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            VALUE: 5,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("5")


@test
async def methods_with_config(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test increment, decrement, and reset methods with configuration."""
    config = {
        DOMAIN: {
            "test": {
                CONF_NAME: "Hello World",
                CONF_INITIAL: 10,
                CONF_STEP: 5,
                CONF_MINIMUM: 5,
                CONF_MAXIMUM: 20,
            }
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()

    entity_id = "counter.test"

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(10)

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(15)

    async_increment(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(20)

    async_decrement(hass, entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    expect(int(state.state)).to_equal(15)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            VALUE: 5,
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("5")

    async with expect_raises_async(
        ValueError, match=r"Value 25 for counter.test exceeding the maximum value of 20"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                VALUE: 25,
            },
            blocking=True,
        )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("5")

    async with expect_raises_async(
        ValueError, match=r"Value 0 for counter.test exceeding the minimum value of 5"
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                VALUE: 0,
            },
            blocking=True,
        )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("5")

    async with expect_raises_async(
        ValueError,
        match=r"Value 6 for counter.test is not a multiple of the step size 5",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                VALUE: 6,
            },
            blocking=True,
        )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("5")


@test
async def initial_state_overrules_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass, (State("counter.test1", "11"), State("counter.test2", "-22"))
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "test1": {CONF_RESTORE: False},
                "test2": {CONF_INITIAL: 10, CONF_RESTORE: False},
            }
        },
    )

    state = hass.states.get("counter.test1")
    expect(state).to_be_truthy()
    expect(int(state.state)).to_equal(0)

    state = hass.states.get("counter.test2")
    expect(state).to_be_truthy()
    expect(int(state.state)).to_equal(10)


@test
async def restore_state_overrules_initial_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""

    mock_restore_cache(
        hass,
        (
            State("counter.test1", "11"),
            State("counter.test2", "-22"),
        ),
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass, DOMAIN, {DOMAIN: {"test1": {}, "test2": {CONF_INITIAL: 10}, "test3": {}}}
    )

    state = hass.states.get("counter.test1")
    expect(state).to_be_truthy()
    expect(int(state.state)).to_equal(11)

    state = hass.states.get("counter.test2")
    expect(state).to_be_truthy()
    expect(int(state.state)).to_equal(-22)


@test
async def no_initial_state_and_no_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure that entity is create without initial and restore feature."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_STEP: 5}}})

    state = hass.states.get("counter.test1")
    expect(state).to_be_truthy()
    expect(int(state.state)).to_equal(0)


@test
async def counter_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that counter context works."""
    expect(
        await async_setup_component(hass, DOMAIN, {"counter": {"test": {}}})
    ).to_be_truthy()

    state = hass.states.get("counter.test")
    expect(state).to_be_truthy()

    await hass.services.async_call(
        DOMAIN,
        "increment",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    expect(state2).to_be_truthy()
    expect(state.state != state2.state).to_be(True)
    expect(state2.context.user_id).to_equal(hass_admin_user.id)


@test
async def counter_min(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that min works."""
    expect(
        await async_setup_component(
            hass, DOMAIN, {"counter": {"test": {"minimum": "0", "initial": "0"}}}
        )
    ).to_be_truthy()

    state = hass.states.get("counter.test")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("0")

    await hass.services.async_call(
        DOMAIN,
        "decrement",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    expect(state2).to_be_truthy()
    expect(state2.state).to_equal("0")

    await hass.services.async_call(
        DOMAIN,
        "increment",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    expect(state2).to_be_truthy()
    expect(state2.state).to_equal("1")


@test
async def counter_max(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that max works."""
    expect(
        await async_setup_component(
            hass, DOMAIN, {"counter": {"test": {"maximum": "0", "initial": "0"}}}
        )
    ).to_be_truthy()

    state = hass.states.get("counter.test")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("0")

    await hass.services.async_call(
        DOMAIN,
        "increment",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    expect(state2).to_be_truthy()
    expect(state2.state).to_equal("0")

    await hass.services.async_call(
        DOMAIN,
        "decrement",
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("counter.test")
    expect(state2).to_be_truthy()
    expect(state2.state).to_equal("-1")


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be_truthy()
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(int(state.state)).to_equal(10)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be_truthy()


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(
            config={
                DOMAIN: {
                    "from_yaml": {
                        "minimum": 1,
                        "maximum": 10,
                        "initial": 5,
                        "step": 1,
                        "restore": False,
                    }
                }
            }
        )
    ).to_be_truthy()

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(int(state.state)).to_equal(10)
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("from storage")
    expect(state.attributes[ATTR_EDITABLE]).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(int(state.state)).to_equal(5)
    expect(state.attributes[ATTR_EDITABLE]).to_be(False)


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(
        await storage_setup(
            config={
                DOMAIN: {
                    "from_yaml": {
                        "minimum": 1,
                        "maximum": 10,
                        "initial": 5,
                        "step": 1,
                        "restore": False,
                    }
                }
            }
        )
    ).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/list"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    storage_ent = "from_storage"
    yaml_ent = "from_yaml"
    result = {item["id"]: item for item in resp["result"]}

    expect(len(result)).to_equal(1)
    expect(storage_ent in result).to_be(True)
    expect(yaml_ent not in result).to_be(True)
    expect(result[storage_ent][ATTR_NAME]).to_equal("from storage")


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test WS delete cleans up entity registry."""
    expect(await storage_setup()).to_be_truthy()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_truthy()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None
    ).to_be(True)

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
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test updating min/max updates the state."""

    settings = {
        "initial": 15,
        "name": "from storage",
        "maximum": 100,
        "minimum": 10,
        "step": 3,
        "restore": True,
    }
    items = [{"id": "from_storage"} | settings]
    expect(await storage_setup(items)).to_be_truthy()

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_truthy()
    expect(int(state.state)).to_equal(15)
    expect(state.attributes[ATTR_MAXIMUM]).to_equal(100)
    expect(state.attributes[ATTR_MINIMUM]).to_equal(10)
    expect(state.attributes[ATTR_STEP]).to_equal(3)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None
    ).to_be(True)

    client = await hass_ws_client(hass)

    updated_settings = settings | {"minimum": 19}
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
    expect(int(state.state)).to_equal(19)
    expect(state.attributes[ATTR_MINIMUM]).to_equal(19)
    expect(state.attributes[ATTR_MAXIMUM]).to_equal(100)
    expect(state.attributes[ATTR_STEP]).to_equal(3)

    updated_settings = settings | {"maximum": 5, "minimum": 2, "step": 5}
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
    expect(int(state.state)).to_equal(5)
    expect(state.attributes[ATTR_MINIMUM]).to_equal(2)
    expect(state.attributes[ATTR_MAXIMUM]).to_equal(5)
    expect(state.attributes[ATTR_STEP]).to_equal(5)

    updated_settings = settings | {"maximum": None, "minimum": None, "step": 6}
    await client.send_json(
        {
            "id": 8,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal({"id": "from_storage"} | updated_settings)

    state = hass.states.get(input_entity_id)
    expect(int(state.state)).to_equal(5)
    expect(ATTR_MINIMUM not in state.attributes).to_be(True)
    expect(ATTR_MAXIMUM not in state.attributes).to_be(True)
    expect(state.attributes[ATTR_STEP]).to_equal(6)


@test
async def create(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test creating counter using WS."""

    items = []

    expect(await storage_setup(items)).to_be_truthy()

    counter_id = "new_counter"
    input_entity_id = f"{DOMAIN}.{counter_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, counter_id)).to_be_none()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 6, "type": f"{DOMAIN}/create", "name": "new counter"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(int(state.state)).to_equal(0)
    expect(ATTR_MINIMUM not in state.attributes).to_be(True)
    expect(ATTR_MAXIMUM not in state.attributes).to_be(True)
    expect(state.attributes[ATTR_STEP]).to_equal(1)
