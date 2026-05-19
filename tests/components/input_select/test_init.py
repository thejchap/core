"""The tests for the Input select component."""

from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.input_select import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    CONF_INITIAL,
    DOMAIN,
    SERVICE_SELECT_FIRST,
    SERVICE_SELECT_LAST,
    SERVICE_SELECT_NEXT,
    SERVICE_SELECT_OPTION,
    SERVICE_SELECT_PREVIOUS,
    SERVICE_SET_OPTIONS,
)
from homeassistant.const import (
    ATTR_EDITABLE,
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_ICON,
    ATTR_NAME,
    SERVICE_RELOAD,
)
from homeassistant.core import Context, HomeAssistant, State
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import storage_setup as storage_setup_fx

from tests.common import MockUser, mock_restore_cache
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
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


@test.cases(
    test.case("none", invalid_config=None),
    test.case("name_with_space", invalid_config={"name with space": None}),
    test.case(
        "bad_initial",
        invalid_config={"bad_initial": {"options": [1, 2], "initial": 3}},
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
async def select_option(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test select_option methods."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {"test_1": {"options": ["some option", "another option"]}}},
        )
    ).to_be(True)
    entity_id = "input_select.test_1"

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("some option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "another option"},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("another option")

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "non existing option"},
            blocking=True,
        )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("another option")


@test
async def select_next(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test select_next methods."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    }
                }
            },
        )
    ).to_be(True)
    entity_id = "input_select.test_1"

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_NEXT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("last option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_NEXT,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("first option")


@test
async def select_previous(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test select_previous methods."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    }
                }
            },
        )
    ).to_be(True)
    entity_id = "input_select.test_1"

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_PREVIOUS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("first option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_PREVIOUS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("last option")


@test
async def select_first_last(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test select_first and _last methods."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    }
                }
            },
        )
    ).to_be(True)
    entity_id = "input_select.test_1"

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_FIRST,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("first option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_LAST,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("last option")


@test
async def config_options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test configuration options."""
    count_start = len(hass.states.async_entity_ids())

    test_2_options = ["Good Option", "Better Option", "Best Option"]

    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {"options": [1, 2]},
                    "test_2": {
                        "name": "Hello World",
                        "icon": "mdi:work",
                        "options": test_2_options,
                        "initial": "Better Option",
                    },
                }
            },
        )
    ).to_be(True)

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_select.test_1")
    state_2 = hass.states.get("input_select.test_2")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()

    expect(state_1.state).to_equal("1")
    expect(state_1.attributes.get(ATTR_OPTIONS)).to_equal(["1", "2"])
    expect(ATTR_ICON in state_1.attributes).to_be(False)

    expect(state_2.state).to_equal("Better Option")
    expect(state_2.attributes.get(ATTR_OPTIONS)).to_equal(test_2_options)
    expect(state_2.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("Hello World")
    expect(state_2.attributes.get(ATTR_ICON)).to_equal("mdi:work")


@test
async def set_options_service(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test set_options service."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    }
                }
            },
        )
    ).to_be(True)
    entity_id = "input_select.test_1"

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OPTIONS,
        {ATTR_OPTIONS: ["first option", "middle option"], ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_OPTIONS,
        {ATTR_OPTIONS: ["test1", "test2"], ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("test1")

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "first option"},
            blocking=True,
        )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("test1")

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "test2"},
        blocking=True,
    )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("test2")


@test
async def set_options_service_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test set_options service with duplicates."""
    expect(
        await async_setup_component(
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test_1": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    }
                }
            },
        )
    ).to_be(True)
    entity_id = "input_select.test_1"

    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")
    expect(state.attributes[ATTR_OPTIONS]).to_equal(
        ["first option", "middle option", "last option"]
    )

    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_OPTIONS,
            {ATTR_OPTIONS: ["option1", "option1"], ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    state = hass.states.get(entity_id)
    expect(state.state).to_equal("middle option")
    expect(state.attributes[ATTR_OPTIONS]).to_equal(
        ["first option", "middle option", "last option"]
    )


@test
async def restore_state(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (
            State("input_select.s1", "last option"),
            State("input_select.s2", "bad option"),
        ),
    )

    options = {"options": ["first option", "middle option", "last option"]}

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"s1": options, "s2": options}})

    state = hass.states.get("input_select.s1")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("last option")

    state = hass.states.get("input_select.s2")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("first option")


@test
async def initial_state_overrules_restore_state(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Ensure states are restored on startup."""
    mock_restore_cache(
        hass,
        (
            State("input_select.s1", "last option"),
            State("input_select.s2", "bad option"),
        ),
    )

    options = {
        "options": ["first option", "middle option", "last option"],
        "initial": "middle option",
    }

    await async_setup_component(hass, DOMAIN, {DOMAIN: {"s1": options, "s2": options}})

    state = hass.states.get("input_select.s1")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("middle option")

    state = hass.states.get("input_select.s2")
    expect(state).not_.to_be_none()
    expect(state.state).to_equal("middle option")


@test
async def input_select_context(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fx),
) -> None:
    """Test that input_select context works."""
    expect(
        await async_setup_component(
            hass,
            "input_select",
            {
                "input_select": {
                    "s1": {"options": ["first option", "middle option", "last option"]}
                }
            },
        )
    ).to_be(True)

    state = hass.states.get("input_select.s1")
    expect(state).not_.to_be_none()

    await hass.services.async_call(
        "input_select",
        "select_next",
        {"entity_id": state.entity_id},
        True,
        Context(user_id=hass_admin_user.id),
    )

    state2 = hass.states.get("input_select.s1")
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
                    "test_1": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    },
                    "test_2": {
                        "options": ["an option", "not an option"],
                        "initial": "an option",
                    },
                }
            },
        )
    ).to_be(True)

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_select.test_1")
    state_2 = hass.states.get("input_select.test_2")
    state_3 = hass.states.get("input_select.test_3")

    expect(state_1).not_.to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).to_be_none()
    expect(state_1.state).to_equal("middle option")
    expect(state_2.state).to_equal("an option")
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2")
    ).not_.to_be_none()
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")).to_be_none()

    with patch(
        "homeassistant.config.load_yaml_config_file",
        autospec=True,
        return_value={
            DOMAIN: {
                "test_2": {
                    "options": ["an option", "reloaded option"],
                    "initial": "reloaded option",
                },
                "test_3": {
                    "options": ["new option", "newer option"],
                    "initial": "newer option",
                },
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

    expect(count_start + 2).to_equal(len(hass.states.async_entity_ids()))

    state_1 = hass.states.get("input_select.test_1")
    state_2 = hass.states.get("input_select.test_2")
    state_3 = hass.states.get("input_select.test_3")

    expect(state_1).to_be_none()
    expect(state_2).not_.to_be_none()
    expect(state_3).not_.to_be_none()
    expect(state_2.state).to_equal("an option")
    expect(state_3.state).to_equal("newer option")
    expect(entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_1")).to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_2")
    ).not_.to_be_none()
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, "test_3")
    ).not_.to_be_none()


@test
async def load_from_storage(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test set up from storage."""
    expect(await storage_setup()).to_be(True)
    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("storage option 1")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)
    expect(state.attributes.get(ATTR_OPTIONS)).to_equal(
        ["storage option 1", "storage option 2"]
    )


@test
async def load_from_storage_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test set up from old storage with duplicates."""
    items = [
        {
            "id": "from_storage",
            "name": "from storage",
            "options": ["yaml update 1", "yaml update 2", "yaml update 2"],
        }
    ]
    expect(await storage_setup(items, minor_version=1)).to_be(True)

    expect(caplog.text).to_contain(
        "Input select 'from storage' with options "
        "['yaml update 1', 'yaml update 2', 'yaml update 2'] "
        "had duplicated options, the duplicates have been removed"
    )

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("yaml update 1")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)
    expect(state.attributes.get(ATTR_OPTIONS)).to_equal(
        ["yaml update 1", "yaml update 2"]
    )


@test
async def editable_state_attribute(
    hass: HomeAssistant = Depends(hass_fixture),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test editable attribute."""
    expect(
        await storage_setup(
            config={DOMAIN: {"from_yaml": {"options": ["yaml option", "other option"]}}}
        )
    ).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_storage")
    expect(state.state).to_equal("storage option 1")
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("from storage")
    expect(state.attributes.get(ATTR_EDITABLE)).to_be(True)

    state = hass.states.get(f"{DOMAIN}.from_yaml")
    expect(state.state).to_equal("yaml option")
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
            config={DOMAIN: {"from_yaml": {"options": ["yaml option"]}}}
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
    """Test updating options updates the state."""

    settings = {
        "name": "from storage",
        "options": ["yaml update 1", "yaml update 2"],
    }
    items = [{"id": "from_storage"} | settings]
    expect(await storage_setup(items)).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(["yaml update 1", "yaml update 2"])
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    updated_settings = settings | {
        "options": ["new option", "newer option"],
        CONF_INITIAL: "newer option",
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
    expect(state.attributes[ATTR_OPTIONS]).to_equal(["new option", "newer option"])

    # Should fail because the initial state is now invalid
    updated_settings = settings | {
        "options": ["new option", "no newer option"],
        CONF_INITIAL: "newer option",
    }
    await client.send_json(
        {
            "id": 7,
            "type": f"{DOMAIN}/update",
            f"{DOMAIN}_id": f"{input_id}",
            **updated_settings,
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(False)


@test
async def update_duplicates(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test updating options updates the state."""

    settings = {
        "name": "from storage",
        "options": ["yaml update 1", "yaml update 2"],
    }
    items = [{"id": "from_storage"} | settings]
    expect(await storage_setup(items)).to_be(True)

    input_id = "from_storage"
    input_entity_id = f"{DOMAIN}.{input_id}"

    state = hass.states.get(input_entity_id)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(["yaml update 1", "yaml update 2"])
    expect(
        entity_registry.async_get_entity_id(DOMAIN, DOMAIN, input_id)
    ).not_.to_be_none()

    client = await hass_ws_client(hass)

    updated_settings = settings | {
        "options": ["new option", "newer option", "newer option"],
        CONF_INITIAL: "newer option",
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
    expect(resp["success"]).to_be(False)
    expect(resp["error"]["code"]).to_equal("home_assistant_error")
    expect(resp["error"]["message"]).to_equal("Duplicate options are not allowed")

    state = hass.states.get(input_entity_id)
    expect(state.attributes[ATTR_OPTIONS]).to_equal(["yaml update 1", "yaml update 2"])


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
            "options": ["new option", "even newer option"],
            "initial": "even newer option",
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(True)

    state = hass.states.get(input_entity_id)
    expect(state.state).to_equal("even newer option")
    expect(state.attributes[ATTR_OPTIONS]).to_equal(["new option", "even newer option"])


@test
async def ws_create_duplicates(
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    storage_setup: Callable[..., Awaitable[bool]] = Depends(storage_setup_fx),
) -> None:
    """Test create WS with duplicates."""
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
            "options": ["new option", "even newer option", "even newer option"],
            "initial": "even newer option",
        }
    )
    resp = await client.receive_json()
    expect(resp["success"]).to_be(False)
    expect(resp["error"]["code"]).to_equal("home_assistant_error")
    expect(resp["error"]["message"]).to_equal("Duplicate options are not allowed")

    expect(hass.states.get(input_entity_id)).to_be_none()


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

    expect(count_start).to_equal(len(hass.states.async_entity_ids()))
