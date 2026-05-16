"""The tests for frontend storage."""

import asyncio
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.frontend import DOMAIN
from homeassistant.components.frontend.storage import async_user_store
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.setup import async_setup_component

from tests.common import MockUser
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_admin_user as hass_admin_user_fixture,
    hass_read_only_access_token as hass_read_only_access_token_fixture,
    hass_storage as hass_storage_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@fixture
async def setup_frontend(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Fixture to setup the frontend."""
    await async_setup_component(hass, "frontend", {})


@test
async def get_user_data_empty(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get_user_data command."""
    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 5, "type": "frontend/get_user_data", "key": "non-existing-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_be(None)


@test
async def get_user_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test get_user_data command."""
    storage_key = f"{DOMAIN}.user_data_{hass_admin_user.id}"
    hass_storage[storage_key] = {
        "key": storage_key,
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": [{"foo": "bar"}]},
    }

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value")

    await client.send_json(
        {"id": 7, "type": "frontend/get_user_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"][0]["foo"]).to_equal("bar")

    await client.send_json({"id": 8, "type": "frontend/get_user_data"})

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]["test-key"]).to_equal("test-value")
    expect(res["result"]["value"]["test-complex"][0]["foo"]).to_equal("bar")


@test.cases(
    test.case("empty", subscriptions=[], events=[]),
    test.case(
        "subscribe_all",
        subscriptions=[(1, {}, {})],
        events=[(1, {"test-key": "test-value"})],
    ),
    test.case(
        "subscribe_test_key",
        subscriptions=[(1, {"key": "test-key"}, None)],
        events=[(1, "test-value")],
    ),
    test.case(
        "subscribe_other_key",
        subscriptions=[(1, {"key": "other-key"}, None)],
        events=[],
    ),
)
async def set_user_data_empty(
    subscriptions: list[tuple[int, dict[str, str], Any]],
    events: list[tuple[int, Any]],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test set_user_data command.

    Also test subscribing.
    """
    client = await hass_ws_client(hass)

    for msg_id, key, event_data in subscriptions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "frontend/subscribe_user_data",
            }
            | key
        )

        event = await client.receive_json()
        expect(event).to_equal(
            {
                "id": msg_id,
                "type": "event",
                "event": {"value": event_data},
            }
        )

        res = await client.receive_json()
        expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_be(None)

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_user_data",
            "key": "test-key",
            "value": "test-value",
        }
    )

    for msg_id, event_data in events:
        event = await client.receive_json()
        expect(event).to_equal(
            {"id": msg_id, "type": "event", "event": {"value": event_data}}
        )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 8, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value")


@test.cases(
    test.case("empty", subscriptions=[], events=[[], []]),
    test.case(
        "subscribe_all",
        subscriptions=[(1, {}, {"test-key": "test-value", "test-complex": "string"})],
        events=[
            [
                (
                    1,
                    {
                        "test-complex": "string",
                        "test-key": "test-value",
                        "test-non-existent-key": "test-value-new",
                    },
                )
            ],
            [
                (
                    1,
                    {
                        "test-complex": [{"foo": "bar"}],
                        "test-key": "test-value",
                        "test-non-existent-key": "test-value-new",
                    },
                )
            ],
        ],
    ),
    test.case(
        "subscribe_test_key",
        subscriptions=[(1, {"key": "test-key"}, "test-value")],
        events=[[], []],
    ),
    test.case(
        "subscribe_test_non_existent",
        subscriptions=[(1, {"key": "test-non-existent-key"}, None)],
        events=[[(1, "test-value-new")], []],
    ),
    test.case(
        "subscribe_test_complex",
        subscriptions=[(1, {"key": "test-complex"}, "string")],
        events=[[], [(1, [{"foo": "bar"}])]],
    ),
    test.case(
        "subscribe_other_key",
        subscriptions=[(1, {"key": "other-key"}, None)],
        events=[[], []],
    ),
)
async def set_user_data(
    subscriptions: list[tuple[int, dict[str, str], Any]],
    events: list[list[tuple[int, Any]]],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test set_user_data command with initial data."""
    storage_key = f"{DOMAIN}.user_data_{hass_admin_user.id}"
    hass_storage[storage_key] = {
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": "string"},
    }

    client = await hass_ws_client(hass)

    for msg_id, key, event_data in subscriptions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "frontend/subscribe_user_data",
            }
            | key
        )

        event = await client.receive_json()
        expect(event).to_equal(
            {
                "id": msg_id,
                "type": "event",
                "event": {"value": event_data},
            }
        )

        res = await client.receive_json()
        expect(res["success"]).to_be(True)

    await client.send_json(
        {
            "id": 5,
            "type": "frontend/set_user_data",
            "key": "test-non-existent-key",
            "value": "test-value-new",
        }
    )

    for msg_id, event_data in events[0]:
        event = await client.receive_json()
        expect(event).to_equal(
            {"id": msg_id, "type": "event", "event": {"value": event_data}}
        )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-non-existent-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value-new")

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_user_data",
            "key": "test-complex",
            "value": [{"foo": "bar"}],
        }
    )

    for msg_id, event_data in events[1]:
        event = await client.receive_json()
        expect(event).to_equal(
            {"id": msg_id, "type": "event", "event": {"value": event_data}}
        )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 8, "type": "frontend/get_user_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"][0]["foo"]).to_equal("bar")

    await client.send_json(
        {"id": 9, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value")


@test
async def get_system_data_empty(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test get_system_data command."""
    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 5, "type": "frontend/get_system_data", "key": "non-existing-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_be(None)


@test
async def get_system_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test get_system_data command."""
    storage_key = f"{DOMAIN}.system_data"
    hass_storage[storage_key] = {
        "key": storage_key,
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": [{"foo": "bar"}]},
    }

    client = await hass_ws_client(hass)

    await client.send_json(
        {"id": 6, "type": "frontend/get_system_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value")

    await client.send_json(
        {"id": 7, "type": "frontend/get_system_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"][0]["foo"]).to_equal("bar")


@test.cases(
    test.case("empty", subscriptions=[], events=[]),
    test.case(
        "subscribe_test_key",
        subscriptions=[(1, {"key": "test-key"}, None)],
        events=[(1, "test-value")],
    ),
    test.case(
        "subscribe_other_key",
        subscriptions=[(1, {"key": "other-key"}, None)],
        events=[],
    ),
)
async def set_system_data_empty(
    subscriptions: list[tuple[int, dict[str, str], Any]],
    events: list[tuple[int, Any]],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test set_system_data command.

    Also test subscribing.
    """
    client = await hass_ws_client(hass)

    for msg_id, key, event_data in subscriptions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "frontend/subscribe_system_data",
            }
            | key
        )

        event = await client.receive_json()
        expect(event).to_equal(
            {
                "id": msg_id,
                "type": "event",
                "event": {"value": event_data},
            }
        )

        res = await client.receive_json()
        expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 6, "type": "frontend/get_system_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_be(None)

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_system_data",
            "key": "test-key",
            "value": "test-value",
        }
    )

    for msg_id, event_data in events:
        event = await client.receive_json()
        expect(event).to_equal(
            {"id": msg_id, "type": "event", "event": {"value": event_data}}
        )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 8, "type": "frontend/get_system_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value")


@test.cases(
    test.case("empty", subscriptions=[], events=[[], []]),
    test.case(
        "subscribe_test_key",
        subscriptions=[(1, {"key": "test-key"}, "test-value")],
        events=[[], []],
    ),
    test.case(
        "subscribe_test_non_existent",
        subscriptions=[(1, {"key": "test-non-existent-key"}, None)],
        events=[[(1, "test-value-new")], []],
    ),
    test.case(
        "subscribe_test_complex",
        subscriptions=[(1, {"key": "test-complex"}, "string")],
        events=[[], [(1, [{"foo": "bar"}])]],
    ),
    test.case(
        "subscribe_other_key",
        subscriptions=[(1, {"key": "other-key"}, None)],
        events=[[], []],
    ),
)
async def set_system_data(
    subscriptions: list[tuple[int, dict[str, str], Any]],
    events: list[list[tuple[int, Any]]],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test set_system_data command with initial data."""
    storage_key = f"{DOMAIN}.system_data"
    hass_storage[storage_key] = {
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": "string"},
    }

    client = await hass_ws_client(hass)

    for msg_id, key, event_data in subscriptions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "frontend/subscribe_system_data",
            }
            | key
        )

        event = await client.receive_json()
        expect(event).to_equal(
            {
                "id": msg_id,
                "type": "event",
                "event": {"value": event_data},
            }
        )

        res = await client.receive_json()
        expect(res["success"]).to_be(True)

    await client.send_json(
        {
            "id": 5,
            "type": "frontend/set_system_data",
            "key": "test-non-existent-key",
            "value": "test-value-new",
        }
    )

    for msg_id, event_data in events[0]:
        event = await client.receive_json()
        expect(event).to_equal(
            {"id": msg_id, "type": "event", "event": {"value": event_data}}
        )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 6, "type": "frontend/get_system_data", "key": "test-non-existent-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value-new")

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_system_data",
            "key": "test-complex",
            "value": [{"foo": "bar"}],
        }
    )

    for msg_id, event_data in events[1]:
        event = await client.receive_json()
        expect(event).to_equal(
            {"id": msg_id, "type": "event", "event": {"value": event_data}}
        )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)

    await client.send_json(
        {"id": 8, "type": "frontend/get_system_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"][0]["foo"]).to_equal("bar")

    await client.send_json(
        {"id": 9, "type": "frontend/get_system_data", "key": "test-key"}
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(True)
    expect(res["result"]["value"]).to_equal("test-value")


@test
async def set_system_data_requires_admin(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    hass_read_only_access_token: str = Depends(hass_read_only_access_token_fixture),
) -> None:
    """Test set_system_data requires admin permissions."""
    client = await hass_ws_client(hass, hass_read_only_access_token)

    await client.send_json(
        {
            "id": 5,
            "type": "frontend/set_system_data",
            "key": "test-key",
            "value": "test-value",
        }
    )

    res = await client.receive_json()
    expect(res["success"]).to_be(False)
    expect(res["error"]["code"]).to_equal("unauthorized")
    expect(res["error"]["message"]).to_equal("Unauthorized")


@test
async def user_store_concurrent_access(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test that concurrent access to user store returns loaded data."""
    storage_key = f"{DOMAIN}.user_data_{hass_admin_user.id}"
    hass_storage[storage_key] = {
        "version": 1,
        "data": {"test-key": "test-value"},
    }

    load_count = 0
    original_async_load = Store.async_load

    async def slow_async_load(self: Store) -> Any:
        """Simulate slow loading to trigger race condition."""
        nonlocal load_count
        load_count += 1
        await asyncio.sleep(0)
        return await original_async_load(self)

    with patch.object(Store, "async_load", slow_async_load):
        results = await asyncio.gather(
            async_user_store(hass, hass_admin_user.id),
            async_user_store(hass, hass_admin_user.id),
            async_user_store(hass, hass_admin_user.id),
        )

    expect(results[0] is results[1] is results[2]).to_be(True)
    expect(results[0].data).to_equal({"test-key": "test-value"})
    expect(load_count).to_equal(1)


@test
async def user_store_load_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test that load errors are propagated and allow retry."""

    async def failing_async_load(self: Store) -> Any:
        """Simulate a load failure."""
        raise OSError("Storage read error")

    with patch.object(Store, "async_load", failing_async_load):
        async with expect_raises_async(OSError, match="Storage read error"):
            await async_user_store(hass, hass_admin_user.id)

    store = await async_user_store(hass, hass_admin_user.id)
    expect(store.data).to_equal({})


@test
async def user_store_concurrent_load_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_frontend),
    hass_admin_user: MockUser = Depends(hass_admin_user_fixture),
) -> None:
    """Test that concurrent callers all receive the same error."""

    async def failing_async_load(self: Store) -> Any:
        """Simulate a slow load failure."""
        await asyncio.sleep(0)
        raise OSError("Storage read error")

    with patch.object(Store, "async_load", failing_async_load):
        results = await asyncio.gather(
            async_user_store(hass, hass_admin_user.id),
            async_user_store(hass, hass_admin_user.id),
            async_user_store(hass, hass_admin_user.id),
            return_exceptions=True,
        )

    expect(len(results)).to_equal(3)
    for result in results:
        expect(isinstance(result, OSError)).to_be(True)
        expect(str(result)).to_equal("Storage read error")

    store = await async_user_store(hass, hass_admin_user.id)
    expect(store.data).to_equal({})
