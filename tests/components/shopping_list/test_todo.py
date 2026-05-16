"""Test shopping list todo platform."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.todo import (
    ATTR_ITEM,
    ATTR_RENAME,
    ATTR_STATUS,
    DOMAIN as TODO_DOMAIN,
    TodoServices,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from ._fixtures import sl_setup as sl_setup_fixture

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

TEST_ENTITY = "todo.shopping_list"

type WsGetItemsType = Callable[[], Coroutine[Any, Any, list[dict[str, str]]]]
type WsMoveItemType = Callable[[str, str | None], Coroutine[Any, Any, dict[str, Any]]]


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@fixture
async def ws_get_items(
    hass_ws_client=Depends(hass_ws_client_fixture),
) -> WsGetItemsType:
    """Fixture to fetch items from the todo websocket."""

    async def get() -> list[dict[str, str]]:
        client = await hass_ws_client()
        await client.send_json_auto_id(
            {
                "type": "todo/item/list",
                "entity_id": TEST_ENTITY,
            }
        )
        resp = await client.receive_json()
        assert resp.get("success")
        return resp.get("result", {}).get("items", [])

    return get


@fixture
async def ws_move_item(
    hass_ws_client=Depends(hass_ws_client_fixture),
) -> WsMoveItemType:
    """Fixture to move an item in the todo list."""

    async def move(uid: str, previous_uid: str | None) -> dict[str, Any]:
        client = await hass_ws_client()
        data: dict[str, Any] = {
            "type": "todo/item/move",
            "entity_id": TEST_ENTITY,
            "uid": uid,
        }
        if previous_uid is not None:
            data["previous_uid"] = previous_uid
        await client.send_json_auto_id(data)
        return await client.receive_json()

    return move


@test
async def get_items(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test creating a shopping list item with the WS API and verifying with To-do API."""
    client = await hass_ws_client(hass)

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("0")

    await client.send_json_auto_id({"type": "shopping_list/items/add", "name": "soda"})
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)
    data = msg["result"]
    expect(data["name"]).to_equal("soda")
    expect(data["complete"]).to_be(False)

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    expect(items[0]["summary"]).to_equal("soda")
    expect(items[0]["status"]).to_equal("needs_action")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("1")


@test
async def add_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test adding shopping_list item and listing it."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    expect(items[0]["summary"]).to_equal("soda")
    expect(items[0]["status"]).to_equal("needs_action")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("1")


@test
async def remove_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test removing a todo item."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )
    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    expect(items[0]["summary"]).to_equal("soda")
    expect(items[0]["status"]).to_equal("needs_action")
    assert "uid" in items[0]

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("1")

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.REMOVE_ITEM,
        {ATTR_ITEM: [items[0]["uid"]]},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(0)

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("0")


@test
async def bulk_remove(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test removing a todo item."""
    for _i in range(5):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.ADD_ITEM,
            {ATTR_ITEM: "soda"},
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )

    items = await ws_get_items()
    expect(len(items)).to_equal(5)
    uids = [item["uid"] for item in items]

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("5")

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.REMOVE_ITEM,
        {ATTR_ITEM: uids},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(0)

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("0")


@test
async def update_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test updating a todo item."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    item = items[0]
    expect(item["summary"]).to_equal("soda")
    expect(item["status"]).to_equal("needs_action")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("1")

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "soda", ATTR_STATUS: "completed"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    item = items[0]
    expect(item["summary"]).to_equal("soda")
    expect(item["status"]).to_equal("completed")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("0")


@test
async def partial_update_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test updating a todo item with partial information."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    item = items[0]
    expect(item["summary"]).to_equal("soda")
    expect(item["status"]).to_equal("needs_action")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("1")

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: item["uid"], ATTR_STATUS: "completed"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    item = items[0]
    expect(item["summary"]).to_equal("soda")
    expect(item["status"]).to_equal("completed")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("0")

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: item["uid"], ATTR_RENAME: "other summary"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    item = items[0]
    expect(item["summary"]).to_equal("other summary")
    expect(item["status"]).to_equal("completed")

    state = hass.states.get(TEST_ENTITY)
    assert state
    expect(state.state).to_equal("0")


@test
async def update_invalid_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
) -> None:
    """Test updating a todo item that does not exist."""
    # Match the bare translation key — todo's exception translations
    # are not pre-loaded under tryke so the resolved message is the key.
    async with expect_raises_async(ServiceValidationError, match="item_not_found"):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.UPDATE_ITEM,
            {ATTR_ITEM: "invalid-uid", ATTR_RENAME: "Example task"},
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )


@test.cases(
    test.case("front_0", 0, None, ["item 1", "item 2", "item 3", "item 4"]),
    test.case("front_1", 1, None, ["item 2", "item 1", "item 3", "item 4"]),
    test.case("front_2", 2, None, ["item 3", "item 1", "item 2", "item 4"]),
    test.case("front_3", 3, None, ["item 4", "item 1", "item 2", "item 3"]),
    test.case("right_0_1", 0, 1, ["item 2", "item 1", "item 3", "item 4"]),
    test.case("right_0_2", 0, 2, ["item 2", "item 3", "item 1", "item 4"]),
    test.case("right_0_3", 0, 3, ["item 2", "item 3", "item 4", "item 1"]),
    test.case("right_1_2", 1, 2, ["item 1", "item 3", "item 2", "item 4"]),
    test.case("right_1_3", 1, 3, ["item 1", "item 3", "item 4", "item 2"]),
    test.case("left_2_0", 2, 0, ["item 1", "item 3", "item 2", "item 4"]),
    test.case("left_3_0", 3, 0, ["item 1", "item 4", "item 2", "item 3"]),
    test.case("left_3_1", 3, 1, ["item 1", "item 2", "item 4", "item 3"]),
    test.case("noop_0_0", 0, 0, ["item 1", "item 2", "item 3", "item 4"]),
    test.case("noop_2_1", 2, 1, ["item 1", "item 2", "item 3", "item 4"]),
    test.case("noop_2_2", 2, 2, ["item 1", "item 2", "item 3", "item 4"]),
    test.case("noop_3_2", 3, 2, ["item 1", "item 2", "item 3", "item 4"]),
    test.case("noop_3_3", 3, 3, ["item 1", "item 2", "item 3", "item 4"]),
)
async def move_item(
    src_idx: int,
    dst_idx: int | None,
    expected_items: list[str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
    ws_move_item: WsMoveItemType = Depends(ws_move_item),
) -> None:
    """Test moving a todo item within the list."""
    for i in range(1, 5):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.ADD_ITEM,
            {ATTR_ITEM: f"item {i}"},
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )

    items = await ws_get_items()
    expect(len(items)).to_equal(4)
    uids = [item["uid"] for item in items]
    summaries = [item["summary"] for item in items]
    expect(summaries).to_equal(["item 1", "item 2", "item 3", "item 4"])

    previous_uid: str | None = None
    if dst_idx is not None:
        previous_uid = uids[dst_idx]

    resp = await ws_move_item(uids[src_idx], previous_uid)
    assert resp.get("success")

    items = await ws_get_items()
    expect(len(items)).to_equal(4)
    summaries = [item["summary"] for item in items]
    expect(summaries).to_equal(expected_items)


@test
async def move_invalid_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    ws_get_items: WsGetItemsType = Depends(ws_get_items),
    ws_move_item: WsMoveItemType = Depends(ws_move_item),
) -> None:
    """Test moving an item that does not exist."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    expect(len(items)).to_equal(1)
    item = items[0]
    expect(item["summary"]).to_equal("soda")

    resp = await ws_move_item("unknown", "0")
    assert not resp.get("success")
    expect(resp.get("error", {}).get("code")).to_equal("failed")
    assert "could not be re-ordered" in resp.get("error", {}).get("message")


@test
async def subscribe_item(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _sl_setup: None = Depends(sl_setup_fixture),
    hass_ws_client=Depends(hass_ws_client_fixture),
) -> None:
    """Test updating a todo item."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "todo/item/subscribe",
            "entity_id": TEST_ENTITY,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None
    subscription_id = msg["id"]

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(subscription_id)
    expect(msg["type"]).to_equal("event")
    items = msg["event"].get("items")
    assert items
    expect(len(items)).to_equal(1)
    expect(items[0]["summary"]).to_equal("soda")
    expect(items[0]["status"]).to_equal("needs_action")
    uid = items[0]["uid"]
    assert uid

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "soda", ATTR_RENAME: "milk"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    msg = await client.receive_json()
    expect(msg["id"]).to_equal(subscription_id)
    expect(msg["type"]).to_equal("event")
    items = msg["event"].get("items")
    assert items
    expect(len(items)).to_equal(1)
    expect(items[0]["summary"]).to_equal("milk")
    expect(items[0]["status"]).to_equal("needs_action")
    assert "uid" in items[0]
