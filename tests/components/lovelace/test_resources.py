"""Test Lovelace resources."""

import copy
from typing import Any
from unittest.mock import ANY, patch
import uuid

from tryke import Depends, expect, fixture, test

from homeassistant.components.lovelace import dashboard, resources
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
    hass_ws_client as hass_ws_client_fx,
)
from tests.typing import WebSocketGenerator

RESOURCE_EXAMPLES = [
    {"type": "js", "url": "/local/bla.js"},
    {"type": "css", "url": "/local/bla.css"},
]


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("lovelace_resources", list_cmd="lovelace/resources"),
    test.case("lovelace_resources_list", list_cmd="lovelace/resources/list"),
)
async def yaml_resources(
    list_cmd: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test defining resources in configuration.yaml."""
    expect(
        await async_setup_component(
            hass,
            "lovelace",
            {"lovelace": {"mode": "yaml", "resources": RESOURCE_EXAMPLES}},
        )
    ).to_be(True)

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(RESOURCE_EXAMPLES)


@test.cases(
    test.case("lovelace_resources", list_cmd="lovelace/resources"),
    test.case("lovelace_resources_list", list_cmd="lovelace/resources/list"),
)
async def yaml_resources_backwards(
    list_cmd: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
) -> None:
    """Test defining resources in YAML ll config (legacy)."""
    with patch(
        "homeassistant.components.lovelace.dashboard.load_yaml_dict",
        return_value={"resources": RESOURCE_EXAMPLES},
    ):
        expect(
            await async_setup_component(
                hass, "lovelace", {"lovelace": {"mode": "yaml"}}
            )
        ).to_be(True)

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(RESOURCE_EXAMPLES)


@test.cases(
    test.case("lovelace_resources", list_cmd="lovelace/resources"),
    test.case("lovelace_resources_list", list_cmd="lovelace/resources/list"),
)
async def storage_resources(
    list_cmd: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test defining resources in storage config."""
    resource_config = [{**item, "id": uuid.uuid4().hex} for item in RESOURCE_EXAMPLES]
    hass_storage[resources.RESOURCE_STORAGE_KEY] = {
        "key": resources.RESOURCE_STORAGE_KEY,
        "version": 1,
        "data": {"items": resource_config},
    }
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(resource_config)


@test.cases(
    test.case("lovelace_resources", list_cmd="lovelace/resources"),
    test.case("lovelace_resources_list", list_cmd="lovelace/resources/list"),
)
async def storage_resources_import(
    list_cmd: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test importing resources from storage config."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "key": "lovelace",
        "version": 1,
        "data": {"config": {"resources": copy.deepcopy(RESOURCE_EXAMPLES)}},
    }

    client = await hass_ws_client(hass)

    # Subscribe
    await client.send_json_auto_id({"type": "lovelace/resources/subscribe"})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"] is None).to_be(True)
    event_id = response["id"]

    response = await client.receive_json()
    expect(response["id"]).to_equal(event_id)
    expect(response["event"]).to_equal([])

    # Fetch data - this also loads the resources
    await client.send_json_auto_id({"type": list_cmd})

    response = await client.receive_json()
    expect(response["id"]).to_equal(event_id)
    expect(response["event"]).to_equal(
        [
            {
                "change_type": "added",
                "item": {
                    "id": ANY,
                    "type": "js",
                    "url": "/local/bla.js",
                },
                "resource_id": ANY,
            },
            {
                "change_type": "added",
                "item": {
                    "id": ANY,
                    "type": "css",
                    "url": "/local/bla.css",
                },
                "resource_id": ANY,
            },
        ]
    )

    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal(
        hass_storage[resources.RESOURCE_STORAGE_KEY]["data"]["items"]
    )
    expect(
        "resources"
        not in hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT]["data"]["config"]
    ).to_be(True)

    # Add a resource
    await client.send_json_auto_id(
        {
            "type": "lovelace/resources/create",
            "res_type": "module",
            "url": "/local/yo.js",
        }
    )
    response = await client.receive_json()
    expect(response["id"]).to_equal(event_id)
    expect(response["event"]).to_equal(
        [
            {
                "change_type": "added",
                "item": {
                    "id": ANY,
                    "type": "module",
                    "url": "/local/yo.js",
                },
                "resource_id": ANY,
            }
        ]
    )

    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    await client.send_json_auto_id({"type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    last_item = response["result"][-1]
    expect(last_item["type"]).to_equal("module")
    expect(last_item["url"]).to_equal("/local/yo.js")

    # Update a resource
    first_item = response["result"][0]

    await client.send_json_auto_id(
        {
            "type": "lovelace/resources/update",
            "resource_id": first_item["id"],
            "res_type": "css",
            "url": "/local/updated.css",
        }
    )
    response = await client.receive_json()
    expect(response["id"]).to_equal(event_id)
    expect(response["event"]).to_equal(
        [
            {
                "change_type": "updated",
                "item": {
                    "id": first_item["id"],
                    "type": "css",
                    "url": "/local/updated.css",
                },
                "resource_id": first_item["id"],
            }
        ]
    )

    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    await client.send_json_auto_id({"type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    first_item = response["result"][0]
    expect(first_item["type"]).to_equal("css")
    expect(first_item["url"]).to_equal("/local/updated.css")

    # Delete a resource
    await client.send_json_auto_id(
        {
            "type": "lovelace/resources/delete",
            "resource_id": first_item["id"],
        }
    )
    response = await client.receive_json()
    expect(response["id"]).to_equal(event_id)
    expect(response["event"]).to_equal(
        [
            {
                "change_type": "removed",
                "item": {
                    "id": first_item["id"],
                    "type": "css",
                    "url": "/local/updated.css",
                },
                "resource_id": first_item["id"],
            }
        ]
    )

    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    await client.send_json_auto_id({"type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)

    expect(len(response["result"])).to_equal(2)
    expect(first_item["id"] not in (item["id"] for item in response["result"])).to_be(
        True
    )


@test.cases(
    test.case("lovelace_resources", list_cmd="lovelace/resources"),
    test.case("lovelace_resources_list", list_cmd="lovelace/resources/list"),
)
async def storage_resources_import_invalid(
    list_cmd: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test importing resources from storage config."""
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)
    hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT] = {
        "key": "lovelace",
        "version": 1,
        "data": {"config": {"resources": [{"invalid": "resource"}]}},
    }

    client = await hass_ws_client(hass)

    # Fetch data
    await client.send_json({"id": 5, "type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal([])
    expect(
        "resources"
        in hass_storage[dashboard.CONFIG_STORAGE_KEY_DEFAULT]["data"]["config"]
    ).to_be(True)


@test
async def storage_resources_create_preserves_existing(
    hass: HomeAssistant = Depends(hass_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test async_create_item lazy-loads before writing.

    Custom integrations may call async_create_item() during startup before the
    frontend triggers a resource listing. Without a lazy-load guard, the
    collection is empty and async_create_item() overwrites all existing
    resources on disk.
    """
    resource_config = [{**item, "id": uuid.uuid4().hex} for item in RESOURCE_EXAMPLES]
    hass_storage[resources.RESOURCE_STORAGE_KEY] = {
        "key": resources.RESOURCE_STORAGE_KEY,
        "version": 1,
        "data": {"items": resource_config},
    }
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    resource_collection = hass.data[LOVELACE_DATA].resources

    # Directly call async_create_item before any websocket listing
    await resource_collection.async_create_item(
        {"res_type": "module", "url": "/local/new.js"}
    )

    # Existing resources must still be present
    items = resource_collection.async_items()
    expect(len(items)).to_equal(len(resource_config) + 1)
    urls = [item["url"] for item in items]
    for original in resource_config:
        expect(original["url"] in urls).to_be(True)
    expect("/local/new.js" in urls).to_be(True)


@test.cases(
    test.case("lovelace_resources", list_cmd="lovelace/resources"),
    test.case("lovelace_resources_list", list_cmd="lovelace/resources/list"),
)
async def storage_resources_safe_mode(
    list_cmd: str,
    hass: HomeAssistant = Depends(hass_fixture),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test defining resources in storage config."""
    resource_config = [{**item, "id": uuid.uuid4().hex} for item in RESOURCE_EXAMPLES]
    hass_storage[resources.RESOURCE_STORAGE_KEY] = {
        "key": resources.RESOURCE_STORAGE_KEY,
        "version": 1,
        "data": {"items": resource_config},
    }
    expect(await async_setup_component(hass, "lovelace", {})).to_be(True)

    client = await hass_ws_client(hass)
    hass.config.safe_mode = True

    # Fetch data
    await client.send_json({"id": 5, "type": list_cmd})
    response = await client.receive_json()
    expect(response["success"]).to_be(True)
    expect(response["result"]).to_equal([])
