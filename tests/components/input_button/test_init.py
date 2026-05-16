"""The tests for the input_test component."""

from collections.abc import Callable, Coroutine
import logging
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.input_button import DOMAIN, SERVICE_PRESS
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    SERVICE_RELOAD,
    STATE_UNKNOWN,
)
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change
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
                    "test_2": {"name": "Hello World", "icon": "mdi:work"},
                }
            },
        )
    ).to_be_truthy()

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)

    state_1 = hass.states.get("input_button.test_1")
    state_2 = hass.states.get("input_button.test_2")

    expect(state_1).to_be_truthy()
    expect(state_2).to_be_truthy()

    expect(state_1.state).to_equal(STATE_UNKNOWN)
    expect(ATTR_ICON not in state_1.attributes).to_be(True)
    expect(ATTR_FRIENDLY_NAME not in state_1.attributes).to_be(True)

    expect(state_2.state).to_equal(STATE_UNKNOWN)
    expect(state_2.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Hello World")
    expect(state_2.attributes.get(ATTR_ICON)).to_equal("mdi:work")


@test
async def restore_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (State("input_button.b1", "2021-01-01T23:59:59+00:00"),),
    )

    hass.set_state(CoreState.starting)
    mock_component(hass, "recorder")

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"b1": None, "b2": None}})

    state = hass.states.get("input_button.b1")
    expect(state).to_be_truthy()
    expect(state.state).to_equal("2021-01-01T23:59:59+00:00")

    state = hass.states.get("input_button.b2")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)


@test
async def input_button_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that input_button context works."""
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {"update": {}}})
    ).to_be_truthy()

    state = hass.states.get("input_button.update")
    expect(state).to_be_truthy()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("input_button.update")
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
                    "test_2": {"name": "Hello World", "icon": "mdi:work"},
                }
            },
        )
    ).to_be_truthy()

    _LOGGER.debug("ENTITIES: %s", hass.states.async_entity_ids())

    expect(count_start + 2 == len(hass.states.async_entity_ids())).to_be(True)

    state_1 = hass.states.get("input_button.test_1")
    state_2 = hass.states.get("input_button.test_2")
    state_3 = hass.states.get("input_button.test_3")

    expect(state_1).to_be_truthy()
    expect(state_2).to_be_truthy()
    expect(state_3).to_be_none()

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

    state_1 = hass.states.get("input_button.test_1")
    state_2 = hass.states.get("input_button.test_2")
    state_3 = hass.states.get("input_button.test_3")

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


@test
async def reload_not_changing_state(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test reload not changing state."""
    expect(await storage_setup()).to_be_truthy()
    state_changes = []

    def state_changed_listener(entity_id, from_s, to_s):
        state_changes.append(to_s)

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state).to_be_truthy()

    async_track_state_change(hass, [f"{DOMAIN}.from_storage"], state_changed_listener)

    # Pressing button changes state
    await hass.services.async_call(
        DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: state.entity_id},
        True,
    )
    await hass.async_block_till_done()
    expect(len(state_changes)).to_equal(1)

    # Reloading does not
    with patch(
        "homeassistant.config.load_yaml_config_file", autospec=True, return_value={}
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            blocking=True,
        )

    await hass.async_block_till_done()

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state).to_be_truthy()
    expect(len(state_changes)).to_equal(1)


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be_truthy()
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be_truthy()


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(config={DOMAIN: {"from_yaml": None}})
    ).to_be_truthy()

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be_truthy()

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(not state.attributes.get(ATTR_EDITABLE)).to_be(True)


@test
async def ws_list(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test listing via WS."""
    expect(
        await storage_setup(config={DOMAIN: {"from_yaml": None}})
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
async def ws_create_update(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Coroutine[Any, Any, bool]] = Depends(storage_setup_fx),
) -> None:
    """Test creating and updating via WS."""
    expect(await storage_setup(config={DOMAIN: {}})).to_be_truthy()

    client = await hass_ws_client(hass)

    await client.send_json({"id": 7, "type": f"{DOMAIN}/create", "name": "new"})
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(f"{DOMAIN}.new")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("new")

    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "new") is not None
    ).to_be(True)

    await client.send_json(
        {"id": 8, "type": f"{DOMAIN}/update", f"{DOMAIN}_id": "new", "name": "newer"}
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)
    expect(resp["result"]).to_equal({"id": "new", "name": "newer"})

    state = hass.states.get(f"{DOMAIN}.new")
    expect(state).to_be_truthy()
    expect(state.state).to_equal(STATE_UNKNOWN)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("newer")

    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "new") is not None
    ).to_be(True)


@test
async def ws_delete(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
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
async def setup_no_config(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test component setup with no config."""
    count_start = len(hass.states.async_entity_ids())
    expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()

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
