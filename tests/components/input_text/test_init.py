"""The tests for the Input text component."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.input_text import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_VALUE,
    CONF_INITIAL,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    DOMAIN,
    MODE_TEXT,
    SERVICE_SET_VALUE,
)
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_NAME,
    SERVICE_RELOAD,
)
from homeassistant.core import Context, CoreState, HomeAssistant, State
from homeassistant.exceptions import Unauthorized
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockUser, mock_restore_cache
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fx,
    hass_read_only_user as hass_read_only_user_fx,
    hass_ws_client as hass_ws_client_fx,
    entity_registry as entity_registry_fx,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator

TEST_VAL_MIN = 2
TEST_VAL_MAX = 22


@fixture
def _trigger_executor() -> int:
    return 0


async def async_set_value(hass: HomeAssistant, entity_id: str, value: str) -> None:
    """Set input_text to value."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: value},
        blocking=True,
    )


@test.cases(
    test.case("none", invalid_config=None),
    test.case("name_with_space", invalid_config={"name with space": None}),
    test.case("min_greater_than_max", invalid_config={"test_1": {"min": 51, "max": 50}}),
    test.case("min_negative", invalid_config={"test_1": {"min": -1, "max": 100}}),
    test.case("max_too_large", invalid_config={"test_1": {"min": 0, "max": 256}}),
    test.case(
        "initial_too_long",
        invalid_config={"test_1": {"min": 0, "max": 3, "initial": "aaaaa"}},
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
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {"initial": "test", "min": 3, "max": 10},
                    "test_2": {},
                }
            },
        )
    ).to_be(True)
    entity_id = "input_text.test_1"
    entity_id_2 = "input_text.test_2"
    expect(hass.states.get(entity_id).state).to_equal("test")
    expect(hass.states.get(entity_id_2).state).to_equal("unknown")

    for entity in (entity_id, entity_id_2):
        await async_set_value(hass, entity, "testing")
        expect(hass.states.get(entity).state).to_equal("testing")

    # Too long for entity 1
    await async_set_value(hass, entity, "testing too long")
    expect(hass.states.get(entity_id).state).to_equal("testing")

    # Set to empty string
    await async_set_value(hass, entity_id_2, "")
    expect(hass.states.get(entity_id_2).state).to_equal("")


@test
async def mode(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test mode settings."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_default_text": {"initial": "test", "min": 3, "max": 10},
                    "test_explicit_text": {
                        "initial": "test",
                        "min": 3,
                        "max": 10,
                        "mode": "text",
                    },
                    "test_explicit_password": {
                        "initial": "test",
                        "min": 3,
                        "max": 10,
                        "mode": "password",
                    },
                }
            },
        )
    ).to_be(True)

    state = hass.states.get("input_text.test_default_text")
    expect(state).not_.to_be_none()
    expect(state.attributes["mode"]).to_equal("text")

    state = hass.states.get("input_text.test_explicit_text")
    expect(state).not_.to_be_none()
    expect(state.attributes["mode"]).to_equal("text")

    state = hass.states.get("input_text.test_explicit_password")
    expect(state).not_.to_be_none()
    expect(state.attributes["mode"]).to_equal("password")


@test
async def restore_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (State("input_text.b1", "test"), State("input_text.b2", "testing too long")),
    )

    hass.set_state(CoreState.starting)

    expect(
        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"b1": None, "b2": {"min": 0, "max": 10}}}
        )
    ).to_be(True)

    state = hass.states.get("input_text.b1")
    expect(state).not_.to_be_none()
    expect(str(state.state)).to_equal("test")

    state = hass.states.get("input_text.b2")
    expect(state).not_.to_be_none()
    expect(str(state.state)).to_equal("unknown")


@test
async def initial_state_overrules_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (State("input_text.b1", "testing"), State("input_text.b2", "testing too long")),
    )

    hass.set_state(CoreState.starting)

    await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "b1": {"initial": "test", "min": 0, "max": 10},
                "b2": {"initial": "test", "min": 0, "max": 10},
            }
        },
    )

    state = hass.states.get("input_text.b1")
    expect(state).not_.to_be_none()
    expect(str(state.state)).to_equal("test")

    state = hass.states.get("input_text.b2")
    expect(state).not_.to_be_none()
    expect(str(state.state)).to_equal("test")


@test
async def no_initial_state_and_no_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure that entity is create without initial and restore feature."""
    hass.set_state(CoreState.starting)

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"b1": {"min": 0, "max": 100}}})

    state = hass.states.get("input_text.b1")
    expect(state).not_.to_be_none()
    expect(str(state.state)).to_equal("unknown")


@test
async def input_text_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that input_text context works."""
    expect(
        await async_setup_component(
            hass, "input_text", {"input_text": {"t1": {"initial": "bla"}}}
        )
    ).to_be(True)

    state = hass.states.get("input_text.t1")
    expect(state).not_.to_be_none()

    await hass.services.async_call(
        "input_text",
        "set_value",
        {"entity_id": state.entity_id, "value": "new_value"},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("input_text.t1")
    expect(state2).not_.to_be_none()
    expect(state.state != state2.state).to_be(True)
    expect(state2.context.user_id).to_equal(hass_admin_user.id)


@test
async def config_none(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Set up input_text without any config."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {"b1": None}})

    state = hass.states.get("input_text.b1")
    expect(state).not_.to_be_none()
    expect(str(state.state)).to_equal("unknown")

    # with empty config we still should have the defaults
    expect(state.attributes[ATTR_MODE]).to_equal(MODE_TEXT)
    expect(state.attributes[ATTR_MAX]).to_equal(CONF_MAX_VALUE)
    expect(state.attributes[ATTR_MIN]).to_equal(CONF_MIN_VALUE)


@test
async def reload(
    hass: HomeAssistant = Depends(hass_fixture),
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
                    "test_1": {"initial": "test 1"},
                    "test_2": {"initial": "test 2"},
                }
            },
        )
    ).to_be(True)

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_text.test_1")
    state_2 = hass.states.get("input_text.test_2")
    state_3 = hass.states.get("input_text.test_3")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).to_be_none()
    expect(state_1.state).to_equal("test 1")
    expect(state_2.state).to_equal("test 2")
    expect(state_1.attributes[ATTR_MIN]).to_equal(0)
    expect(state_2.attributes[ATTR_MAX]).to_equal(100)

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {"initial": "test reloaded", ATTR_MIN: 12},
                "test_3": {"initial": "test 3", ATTR_MAX: 21},
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

    state_1 = hass.states.get("input_text.test_1")
    state_2 = hass.states.get("input_text.test_2")
    state_3 = hass.states.get("input_text.test_3")

    expect(state_1).to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).not_.to_be_none()
    expect(state_2.attributes[ATTR_MIN]).to_equal(12)
    expect(state_3.attributes[ATTR_MAX]).to_equal(21)


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be(True)
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("loaded from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)
    expect(state.attributes[ATTR_MAX]).to_equal(TEST_VAL_MAX)
    expect(state.attributes[ATTR_MIN]).to_equal(TEST_VAL_MIN)


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
                        "initial": "yaml initial value",
                        ATTR_MODE: MODE_TEXT,
                        ATTR_MAX: 33,
                        ATTR_MIN: 3,
                        ATTR_NAME: "yaml friendly name",
                    }
                }
            }
        )
    ).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("loaded from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)
    expect(state.attributes[ATTR_MAX]).to_equal(TEST_VAL_MAX)
    expect(state.attributes[ATTR_MIN]).to_equal(TEST_VAL_MIN)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(state.state).to_equal("yaml initial value")
    expect(state.attributes[ATTR_EDITABLE]).to_be(False)
    expect(state.attributes[ATTR_MAX]).to_equal(33)
    expect(state.attributes[ATTR_MIN]).to_equal(3)


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
                        "initial": "yaml initial value",
                        ATTR_MODE: MODE_TEXT,
                        ATTR_MAX: 33,
                        ATTR_MIN: 3,
                        ATTR_NAME: "yaml friendly name",
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
async def update(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test updating min/max updates the state."""

    expect(await storage_setup()).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("from storage")
    expect(state.attributes[ATTR_MODE]).to_equal(MODE_TEXT)
    expect(state.state).to_equal("loaded from storage")
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    updated_settings = {
        ATTR_NAME: "even newer name",
        CONF_INITIAL: "newer option",
        ATTR_MAX: TEST_VAL_MAX,
        ATTR_MIN: 6,
        ATTR_MODE: "password",
    }
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
    expect(state.state).to_equal("loaded from storage")
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("even newer name")
    expect(state.attributes[ATTR_MODE]).to_equal("password")
    expect(state.attributes[ATTR_MIN]).to_equal(6)
    expect(state.attributes[ATTR_MAX]).to_equal(TEST_VAL_MAX)


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
            "initial": "even newer option",
            ATTR_MAX: 44,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(state.state).to_equal("even newer option")
    expect(state.attributes[ATTR_FRIENDLY_NAME]).to_equal("New Input")
    expect(state.attributes[ATTR_EDITABLE]).to_be(True)
    expect(state.attributes[ATTR_MAX]).to_equal(44)
    expect(state.attributes[ATTR_MIN]).to_equal(0)


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
