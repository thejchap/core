"""Test floor registry API."""

from datetime import datetime
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import floor_registry as fr
from homeassistant.util.dt import utcnow

from ._fixtures import floor_registry_client as floor_registry_client_fx

from tests.hass_fixtures import (
    floor_registry as floor_registry_fx,
    freezer as freezer_fx,
    hass as hass_fixture,
    hass_storage as hass_storage_fx,
)
from tests.typing import MockHAClientWebSocket


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def list_floors(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test list entries."""
    created_1 = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_1)
    floor_registry.async_create("First floor")

    created_2 = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(created_2)
    floor_registry.async_create(
        name="Second floor",
        aliases={"top floor", "attic"},
        icon="mdi:home-floor-2",
        level=2,
    )

    expect(len(floor_registry.floors)).to_equal(2)

    floor_registry.async_update(
        "first_floor",
        name="First floor...",
    )

    await client.send_json_auto_id({"type": "config/floor_registry/list"})

    msg = await client.receive_json()

    expect(len(msg["result"])).to_equal(len(floor_registry.floors))
    expect(msg["result"][0]).to_equal(
        {
            "aliases": [],
            "created_at": created_1.timestamp(),
            "icon": None,
            "floor_id": "first_floor",
            "modified_at": created_2.timestamp(),
            "name": "First floor...",
            "level": None,
        }
    )
    expect(msg["result"][1]).to_equal(
        {
            "aliases": unordered(["top floor", "attic"]),
            "created_at": created_2.timestamp(),
            "icon": "mdi:home-floor-2",
            "floor_id": "second_floor",
            "modified_at": created_2.timestamp(),
            "name": "Second floor",
            "level": 2,
        }
    )


@test
async def create_floor(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test create entry."""
    del freezer
    await client.send_json_auto_id(
        {"type": "config/floor_registry/create", "name": "First floor"}
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "aliases": [],
            "created_at": utcnow().timestamp(),
            "icon": None,
            "floor_id": "first_floor",
            "modified_at": utcnow().timestamp(),
            "name": "First floor",
            "level": None,
        }
    )

    await client.send_json_auto_id(
        {
            "name": "Second floor",
            "type": "config/floor_registry/create",
            "aliases": ["top floor", "attic"],
            "icon": "mdi:home-floor-2",
            "level": 2,
        }
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(2)
    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["top floor", "attic"]),
            "created_at": utcnow().timestamp(),
            "icon": "mdi:home-floor-2",
            "floor_id": "second_floor",
            "modified_at": utcnow().timestamp(),
            "name": "Second floor",
            "level": 2,
        }
    )

    await client.send_json_auto_id(
        {
            "name": "Third floor",
            "type": "config/floor_registry/create",
            "aliases": ["", " "],
            "icon": "mdi:home-floor-2",
            "level": 3,
        }
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(3)
    expect(msg["result"]).to_equal(
        {
            "aliases": [],
            "created_at": utcnow().timestamp(),
            "icon": "mdi:home-floor-2",
            "floor_id": "third_floor",
            "modified_at": utcnow().timestamp(),
            "name": "Third floor",
            "level": 3,
        }
    )


@test
async def create_floor_with_name_already_in_use(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test create entry that should fail."""
    floor_registry.async_create("First floor")
    expect(len(floor_registry.floors)).to_equal(1)

    await client.send_json_auto_id(
        {"name": "First floor", "type": "config/floor_registry/create"}
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal(
        "The name First floor (firstfloor) is already in use"
    )
    expect(len(floor_registry.floors)).to_equal(1)


@test
async def delete_floor(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test delete entry."""
    floor = floor_registry.async_create("First floor")
    expect(len(floor_registry.floors)).to_equal(1)

    await client.send_json_auto_id(
        {"floor_id": floor.floor_id, "type": "config/floor_registry/delete"}
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(bool(floor_registry.floors)).to_be(False)


@test
async def delete_non_existing_floor(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test delete entry that should fail."""
    floor_registry.async_create("First floor")
    expect(len(floor_registry.floors)).to_equal(1)

    await client.send_json_auto_id(
        {
            "floor_id": "zaphotbeeblebrox",
            "type": "config/floor_registry/delete",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("Floor ID doesn't exist")
    expect(len(floor_registry.floors)).to_equal(1)


@test
async def update_floor(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
) -> None:
    """Test update entry."""
    created_at = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_at)
    floor = floor_registry.async_create("First floor")
    expect(len(floor_registry.floors)).to_equal(1)
    modified_at = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "Second floor",
            "aliases": ["top floor", "attic"],
            "icon": "mdi:home-floor-2",
            "type": "config/floor_registry/update",
            "level": 2,
        }
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["top floor", "attic"]),
            "created_at": created_at.timestamp(),
            "icon": "mdi:home-floor-2",
            "floor_id": floor.floor_id,
            "modified_at": modified_at.timestamp(),
            "name": "Second floor",
            "level": 2,
        }
    )

    modified_at = datetime.fromisoformat("2024-07-16T13:50:00.900075+00:00")
    freezer.move_to(modified_at)
    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "First floor",
            "aliases": [],
            "icon": None,
            "level": None,
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "aliases": [],
            "created_at": created_at.timestamp(),
            "icon": None,
            "floor_id": floor.floor_id,
            "modified_at": modified_at.timestamp(),
            "name": "First floor",
            "level": None,
        }
    )

    modified_at = datetime.fromisoformat("2024-07-16T13:55:00.900075+00:00")
    freezer.move_to(modified_at)
    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "First floor",
            "aliases": ["top floor", "attic", "", " "],
            "icon": None,
            "level": None,
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["top floor", "attic"]),
            "created_at": created_at.timestamp(),
            "icon": None,
            "floor_id": floor.floor_id,
            "modified_at": modified_at.timestamp(),
            "name": "First floor",
            "level": None,
        }
    )

    modified_at = datetime.fromisoformat("2024-07-16T13:55:00.900075+00:00")
    freezer.move_to(modified_at)
    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "First floor",
            "aliases": ["top floor", "attic", "solaio "],
            "icon": None,
            "level": None,
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(len(floor_registry.floors)).to_equal(1)
    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["top floor", "attic", "solaio"]),
            "created_at": created_at.timestamp(),
            "icon": None,
            "floor_id": floor.floor_id,
            "modified_at": modified_at.timestamp(),
            "name": "First floor",
            "level": None,
        }
    )


@test
async def update_with_name_already_in_use(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test update entry."""
    floor = floor_registry.async_create("First floor")
    floor_registry.async_create("Second floor")
    expect(len(floor_registry.floors)).to_equal(2)

    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "Second floor",
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal(
        "The name Second floor (secondfloor) is already in use"
    )
    expect(len(floor_registry.floors)).to_equal(2)


@test
async def reorder_floors(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test reorder floors."""
    floor1 = floor_registry.async_create("First floor")
    floor2 = floor_registry.async_create("Second floor")
    floor3 = floor_registry.async_create("Third floor")

    await client.send_json_auto_id({"type": "config/floor_registry/list"})
    msg = await client.receive_json()
    expect([floor["floor_id"] for floor in msg["result"]]).to_equal(
        [floor1.floor_id, floor2.floor_id, floor3.floor_id]
    )

    await client.send_json_auto_id(
        {
            "type": "config/floor_registry/reorder",
            "floor_ids": [floor3.floor_id, floor1.floor_id, floor2.floor_id],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    await client.send_json_auto_id({"type": "config/floor_registry/list"})
    msg = await client.receive_json()
    expect([floor["floor_id"] for floor in msg["result"]]).to_equal(
        [floor3.floor_id, floor1.floor_id, floor2.floor_id]
    )


@test
async def reorder_floors_invalid_floor_ids(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test reorder with invalid floor IDs."""
    floor1 = floor_registry.async_create("First floor")
    floor_registry.async_create("Second floor")

    await client.send_json_auto_id(
        {
            "type": "config/floor_registry/reorder",
            "floor_ids": [floor1.floor_id],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_format")
    expect("must contain all existing floor IDs" in msg["error"]["message"]).to_be(True)


@test
async def reorder_floors_with_nonexistent_id(
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
) -> None:
    """Test reorder with nonexistent floor ID."""
    floor1 = floor_registry.async_create("First floor")
    floor2 = floor_registry.async_create("Second floor")

    await client.send_json_auto_id(
        {
            "type": "config/floor_registry/reorder",
            "floor_ids": [floor1.floor_id, floor2.floor_id, "nonexistent"],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_format")


@test
async def reorder_floors_persistence(
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockHAClientWebSocket = Depends(floor_registry_client_fx),
    floor_registry: fr.FloorRegistry = Depends(floor_registry_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test that floor reordering is persisted."""
    del hass_storage
    floor1 = floor_registry.async_create("First floor")
    floor2 = floor_registry.async_create("Second floor")
    floor3 = floor_registry.async_create("Third floor")

    await client.send_json_auto_id(
        {
            "type": "config/floor_registry/reorder",
            "floor_ids": [floor2.floor_id, floor3.floor_id, floor1.floor_id],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    await hass.async_block_till_done()

    floor_ids = [floor.floor_id for floor in floor_registry.async_list_floors()]
    expect(floor_ids).to_equal([floor2.floor_id, floor3.floor_id, floor1.floor_id])
