"""The tests for the input_boolean component."""

from collections.abc import Callable, Coroutine
import logging
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.input_boolean import CONF_INITIAL, DOMAIN, is_on
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    SERVICE_RELOAD,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockUser, mock_component, mock_restore_cache
from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_ws_client as hass_ws_client_fx,
)
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
async def methods(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test is_on, turn_on, turn_off methods."""
    expect(await async_setup_component(hass, DOMAIN, {DOMAIN: {"test_1": None}})).to_be(
        True
    )
    entity_id = "input_boolean.test_1"

    expect(is_on(hass, entity_id)).to_be(False)

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    expect(is_on(hass, entity_id)).to_be(True)

    await hass.services.async_call(
        DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    expect(is_on(hass, entity_id)).to_be(False)

    await hass.services.async_call(
        DOMAIN, SERVICE_TOGGLE, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    expect(is_on(hass, entity_id)).to_be(True)


@test
async def config_options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": None,
                    "test_2": {
                        "name": "Hello World",
                        "icon": "mdi:work",
                        "initial": True,
                    },
                }
            },
        )
    ).to_be(True)

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)

    state_1 = hass.states.get("input_boolean.test_1")
    state_2 = hass.states.get("input_boolean.test_2")

    expect(state_1 is not None).to_be(True)
    expect(state_2 is not None).to_be(True)

    expect(state_1.state).to_equal(STATE_OFF)
    expect(ATTR_ICON not in state_1.attributes).to_be(True)
    expect(ATTR_FRIENDLY_NAME not in state_1.attributes).to_be(True)

    expect(state_2.state).to_equal(STATE_ON)
    expect(state_2.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Hello World")
    expect(state_2.attributes.get(ATTR_ICON)).to_equal("mdi:work")


@test
async def restore_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (
            State("input_boolean.b1", "on"),
            State("input_boolean.b2", "off"),
            State("input_boolean.b3", "on"),
        ),
    )

    hass.set_state(CoreState.starting)
    mock_component(hass, "recorder")

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"b1": None, "b2": None}})

    state = hass.states.get("input_boolean.b1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("on")

    state = hass.states.get("input_boolean.b2")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("off")


@test
async def initial_state_overrules_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass, (State("input_boolean.b1", "on"), State("input_boolean.b2", "off"))
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass,
        DOMAIN,
        {DOMAIN: {"b1": {CONF_INITIAL: False}, "b2": {CONF_INITIAL: True}}},
    )

    state = hass.states.get("input_boolean.b1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("off")

    state = hass.states.get("input_boolean.b2")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("on")


@test
async def input_boolean_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that input_boolean context works."""
    expect(
        await async_setup_component(
            hass, "input_boolean", {"input_boolean": {"ac": {CONF_INITIAL: True}}}
        )
    ).to_be(True)

    state = hass.states.get("input_boolean.ac")
    expect(state).to_be_truthy()

    await hass.services.async_call(
        "input_boolean",
        "turn_off",
        {"entity_id": state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("input_boolean.ac")
    expect(state2).to_be_truthy()
    expect(state.state != state2.state).to_be(True)
    expect(state2.context.user_id).to_equal(hass_admin_user.id)


@test
async def reload(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test reload service."""
    count_start = len(hass.states.async_entity_ids())

    _LOGGER.debug("ENTITIES @ start: %s", hass.states.async_entity_ids())

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": None,
                    "test_2": {
                        "name": "Hello World",
                        "icon": "mdi:work",
                        "initial": True,
                    },
                }
            },
        )
    ).to_be(True)

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)

    state_1 = hass.states.get("input_boolean.test_1")
    state_2 = hass.states.get("input_boolean.test_2")
    state_3 = hass.states.get("input_boolean.test_3")

    expect(state_1).to_be_truthy()
    expect(state_2).to_be_truthy()
    expect(state_3).to_be_none()
    expect(state_2.state).to_equal(STATE_ON)

    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1") is not None
    ).to_be(True)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    ).to_be(True)
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")).to_be_none()

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    "name": "Hello World reloaded",
                    "icon": "mdi:work_reloaded",
                    "initial": False,
                },
                "test_3": None,
            }
        },
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
            context=Context(user_id=hass_admin_user.id),
        )

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)

    state_1 = hass.states.get("input_boolean.test_1")
    state_2 = hass.states.get("input_boolean.test_2")
    state_3 = hass.states.get("input_boolean.test_3")

    expect(state_1).to_be_none()
    expect(state_2).to_be_truthy()
    expect(state_3).to_be_truthy()

    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2") is not None
    ).to_be(True)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3") is not None
    ).to_be(True)

    expect(state_2.state).to_equal(STATE_ON)
    expect(state_2.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Hello World reloaded")
    expect(state_2.attributes.get(ATTR_ICON)).to_equal("mdi:work_reloaded")


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be(True)
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(await storage_setup(config={DOMAIN: {"from_yaml": None}})).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(state.state).to_equal(STATE_OFF)
    expect(not state.attributes.get(ATTR_EDITABLE)).to_be(True)


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(await storage_setup(config={DOMAIN: {"from_yaml": None}})).to_be(True)

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
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test WS delete cleans up entity registry."""
    expect(await storage_setup()).to_be(True)

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
async def ws_update(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test update WS."""

    settings = {
        "name": "from storage",
    }
    items = [{"id": "from_storage"} | settings]
    expect(await storage_setup(items)).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state).to_be_truthy()
    expect(bool(state.state)).to_be(True)
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id) is not None
    ).to_be(True)

    client = await hass_ws_client(hass)

    updated_settings = settings | {"name": "new_name", "icon": "mdi:blah"}
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
    expect(state.attributes["icon"]).to_equal("mdi:blah")
    expect(state.attributes["friendly_name"]).to_equal("new_name")

    updated_settings = settings | {"name": "new_name_2"}
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
    expect("icon" not in state.attributes).to_be(True)
    expect(state.attributes["friendly_name"]).to_equal("new_name_2")


@test
async def ws_create(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
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
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(bool(state.state)).to_be(True)


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

    expect(count_start == len(hass.states.async_entity_ids())).to_be(True)
