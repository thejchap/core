"""Test category registry API."""

from datetime import datetime

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.helpers import category_registry as cr
from homeassistant.util.dt import utcnow

from ._fixtures import category_registry_client as category_registry_client_fx

from tests.common import ANY
from tests.hass_fixtures import (
    category_registry as category_registry_fx,
    freezer as freezer_fx,
)
from tests.typing import MockHAClientWebSocket


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def list_categories(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test list entries."""
    del freezer
    category1 = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    category2 = category_registry.async_create(
        scope="automation",
        name="Something else",
        icon="mdi:home",
    )
    category3 = category_registry.async_create(
        scope="zone",
        name="Grocery stores",
        icon="mdi:store",
    )

    expect(len(category_registry.categories)).to_equal(2)
    expect(len(category_registry.categories["automation"])).to_equal(2)
    expect(len(category_registry.categories["zone"])).to_equal(1)

    await client.send_json_auto_id(
        {"type": "config/category_registry/list", "scope": "automation"}
    )

    msg = await client.receive_json()

    expect(len(msg["result"])).to_equal(2)
    expect(msg["result"][0]).to_equal(
        {
            "category_id": category1.category_id,
            "created_at": utcnow().timestamp(),
            "modified_at": utcnow().timestamp(),
            "name": "Energy saving",
            "icon": "mdi:leaf",
        }
    )
    expect(msg["result"][1]).to_equal(
        {
            "category_id": category2.category_id,
            "created_at": utcnow().timestamp(),
            "modified_at": utcnow().timestamp(),
            "name": "Something else",
            "icon": "mdi:home",
        }
    )

    await client.send_json_auto_id(
        {"type": "config/category_registry/list", "scope": "zone"}
    )

    msg = await client.receive_json()

    expect(len(msg["result"])).to_equal(1)
    expect(msg["result"][0]).to_equal(
        {
            "category_id": category3.category_id,
            "created_at": utcnow().timestamp(),
            "modified_at": utcnow().timestamp(),
            "name": "Grocery stores",
            "icon": "mdi:store",
        }
    )


@test
async def create_category(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test create entry."""
    created1 = datetime(2024, 2, 14, 12, 0, 0)
    freezer.move_to(created1)
    await client.send_json_auto_id(
        {
            "type": "config/category_registry/create",
            "scope": "automation",
            "name": "Energy saving",
            "icon": "mdi:leaf",
        }
    )

    msg = await client.receive_json()

    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    expect(msg["result"]).to_equal(
        {
            "icon": "mdi:leaf",
            "category_id": ANY,
            "created_at": created1.timestamp(),
            "modified_at": created1.timestamp(),
            "name": "Energy saving",
        }
    )

    created2 = datetime(2024, 3, 14, 12, 0, 0)
    freezer.move_to(created2)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "name": "Something else",
            "type": "config/category_registry/create",
        }
    )

    msg = await client.receive_json()

    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(2)

    expect(msg["result"]).to_equal(
        {
            "icon": None,
            "category_id": ANY,
            "created_at": created2.timestamp(),
            "modified_at": created2.timestamp(),
            "name": "Something else",
        }
    )

    created3 = datetime(2024, 4, 14, 12, 0, 0)
    freezer.move_to(created3)

    await client.send_json_auto_id(
        {
            "type": "config/category_registry/create",
            "scope": "script",
            "name": "Energy saving",
            "icon": "mdi:leaf",
        }
    )

    msg = await client.receive_json()

    expect(len(category_registry.categories)).to_equal(2)
    expect(len(category_registry.categories["automation"])).to_equal(2)
    expect(len(category_registry.categories["script"])).to_equal(1)

    expect(msg["result"]).to_equal(
        {
            "icon": "mdi:leaf",
            "category_id": ANY,
            "created_at": created3.timestamp(),
            "modified_at": created3.timestamp(),
            "name": "Energy saving",
        }
    )


@test
async def create_category_with_name_already_in_use(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
) -> None:
    """Test create entry that should fail."""
    category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "name": "ENERGY SAVING",
            "type": "config/category_registry/create",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal(
        "The name 'ENERGY SAVING' is already in use"
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)


@test
async def delete_category(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
) -> None:
    """Test delete entry."""
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "type": "config/category_registry/delete",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(len(category_registry.categories)).to_equal(1)
    expect(bool(category_registry.categories["automation"])).to_be(False)


@test
async def delete_non_existing_category(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
) -> None:
    """Test delete entry that should fail."""
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": "idkfa",
            "type": "config/category_registry/delete",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("Category ID doesn't exist")
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await client.send_json_auto_id(
        {
            "scope": "bullshizzle",
            "category_id": category.category_id,
            "type": "config/category_registry/delete",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("Category ID doesn't exist")
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)


@test
async def update_category(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test update entry."""
    created = datetime(2024, 2, 14, 12, 0, 0)
    freezer.move_to(created)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    modified = datetime(2024, 3, 14, 12, 0, 0)
    freezer.move_to(modified)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "name": "ENERGY SAVING",
            "icon": "mdi:left",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "icon": "mdi:left",
            "category_id": category.category_id,
            "created_at": created.timestamp(),
            "modified_at": modified.timestamp(),
            "name": "ENERGY SAVING",
        }
    )

    modified = datetime(2024, 4, 14, 12, 0, 0)
    freezer.move_to(modified)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "name": "Energy saving",
            "icon": None,
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "icon": None,
            "category_id": category.category_id,
            "created_at": created.timestamp(),
            "modified_at": modified.timestamp(),
            "name": "Energy saving",
        }
    )


@test
async def update_with_name_already_in_use(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
) -> None:
    """Test update entry."""
    category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )
    category = category_registry.async_create(
        scope="automation",
        name="Something else",
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(2)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "name": "ENERGY SAVING",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal(
        "The name 'ENERGY SAVING' is already in use"
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(2)


@test
async def update_non_existing_category(
    client: MockHAClientWebSocket = Depends(category_registry_client_fx),
    category_registry: cr.CategoryRegistry = Depends(category_registry_fx),
) -> None:
    """Test update entry that should fail."""
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": "idkfa",
            "name": "New category name",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("Category ID doesn't exist")
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await client.send_json_auto_id(
        {
            "scope": "bullshizzle",
            "category_id": category.category_id,
            "name": "New category name",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("Category ID doesn't exist")
    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)
