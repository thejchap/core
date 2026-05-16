"""Test area_registry API."""

from datetime import datetime
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.util.dt import utcnow

from ._fixtures import (
    area_registry_client as area_registry_client_fx,
    mock_temperature_humidity_entity as mock_temperature_humidity_entity_fx,
)

from tests.common import ANY
from tests.hass_fixtures import (
    area_registry as area_registry_fx,
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
async def list_areas(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    _mock_temperature_humidity: None = Depends(mock_temperature_humidity_entity_fx),
) -> None:
    """Test list entries."""
    created_area1 = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_area1)
    area1 = area_registry.async_create("mock 1")

    created_area2 = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(created_area2)
    area2 = area_registry.async_create(
        "mock 2",
        aliases={"alias_1", "alias_2"},
        floor_id="first_floor",
        humidity_entity_id="sensor.mock_humidity",
        icon="mdi:garage",
        labels={"label_1", "label_2"},
        picture="/image/example.png",
        temperature_entity_id="sensor.mock_temperature",
    )

    await client.send_json_auto_id({"type": "config/area_registry/list"})

    msg = await client.receive_json()
    expect(msg["result"]).to_equal(
        [
            {
                "aliases": [],
                "area_id": area1.id,
                "created_at": created_area1.timestamp(),
                "floor_id": None,
                "humidity_entity_id": None,
                "icon": None,
                "labels": [],
                "modified_at": created_area1.timestamp(),
                "name": "mock 1",
                "picture": None,
                "temperature_entity_id": None,
            },
            {
                "aliases": unordered(["alias_1", "alias_2"]),
                "area_id": area2.id,
                "created_at": created_area2.timestamp(),
                "floor_id": "first_floor",
                "humidity_entity_id": "sensor.mock_humidity",
                "icon": "mdi:garage",
                "labels": unordered(["label_1", "label_2"]),
                "modified_at": created_area2.timestamp(),
                "name": "mock 2",
                "picture": "/image/example.png",
                "temperature_entity_id": "sensor.mock_temperature",
            },
        ]
    )


@test
async def create_area(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    _mock_temperature_humidity: None = Depends(mock_temperature_humidity_entity_fx),
) -> None:
    """Test create entry."""
    del freezer
    await client.send_json_auto_id(
        {"name": "mock", "type": "config/area_registry/create"}
    )

    msg = await client.receive_json()

    expect(msg["result"]).to_equal(
        {
            "aliases": [],
            "area_id": ANY,
            "floor_id": None,
            "icon": None,
            "labels": [],
            "name": "mock",
            "picture": None,
            "created_at": utcnow().timestamp(),
            "modified_at": utcnow().timestamp(),
            "temperature_entity_id": None,
            "humidity_entity_id": None,
        }
    )
    expect(len(area_registry.areas)).to_equal(1)

    await client.send_json_auto_id(
        {
            "aliases": ["alias_1", "alias_2"],
            "floor_id": "first_floor",
            "icon": "mdi:garage",
            "labels": ["label_1", "label_2"],
            "name": "mock 2",
            "picture": "/image/example.png",
            "temperature_entity_id": "sensor.mock_temperature",
            "humidity_entity_id": "sensor.mock_humidity",
            "type": "config/area_registry/create",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["alias_1", "alias_2"]),
            "area_id": ANY,
            "floor_id": "first_floor",
            "icon": "mdi:garage",
            "labels": unordered(["label_1", "label_2"]),
            "name": "mock 2",
            "picture": "/image/example.png",
            "created_at": utcnow().timestamp(),
            "modified_at": utcnow().timestamp(),
            "temperature_entity_id": "sensor.mock_temperature",
            "humidity_entity_id": "sensor.mock_humidity",
        }
    )
    expect(len(area_registry.areas)).to_equal(2)

    await client.send_json_auto_id(
        {
            "aliases": [" alias_1 ", "", " "],
            "floor_id": "first_floor",
            "icon": "mdi:garage",
            "labels": ["label_1", "label_2"],
            "name": "mock 3",
            "picture": "/image/example.png",
            "temperature_entity_id": "sensor.mock_temperature",
            "humidity_entity_id": "sensor.mock_humidity",
            "type": "config/area_registry/create",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["alias_1"]),
            "area_id": ANY,
            "floor_id": "first_floor",
            "icon": "mdi:garage",
            "labels": unordered(["label_1", "label_2"]),
            "name": "mock 3",
            "picture": "/image/example.png",
            "created_at": utcnow().timestamp(),
            "modified_at": utcnow().timestamp(),
            "temperature_entity_id": "sensor.mock_temperature",
            "humidity_entity_id": "sensor.mock_humidity",
        }
    )
    expect(len(area_registry.areas)).to_equal(3)


@test
async def create_area_with_name_already_in_use(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test create entry that should fail."""
    area_registry.async_create("mock")

    await client.send_json_auto_id(
        {"name": "mock", "type": "config/area_registry/create"}
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("The name mock (mock) is already in use")
    expect(len(area_registry.areas)).to_equal(1)


@test
async def delete_area(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test delete entry."""
    area = area_registry.async_create("mock")

    await client.send_json(
        {"id": 1, "area_id": area.id, "type": "config/area_registry/delete"}
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(True)
    expect(bool(area_registry.areas)).to_be(False)


@test
async def delete_non_existing_area(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test delete entry that should fail."""
    area_registry.async_create("mock")

    await client.send_json_auto_id(
        {"area_id": "", "type": "config/area_registry/delete"}
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal("Area ID doesn't exist")
    expect(len(area_registry.areas)).to_equal(1)


@test
async def update_area(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
    freezer: FrozenDateTimeFactory = Depends(freezer_fx),
    _mock_temperature_humidity: None = Depends(mock_temperature_humidity_entity_fx),
) -> None:
    """Test update entry."""
    created_at = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_at)
    area = area_registry.async_create("mock 1")
    modified_at = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/update",
            "aliases": ["alias_1", "alias_2"],
            "area_id": area.id,
            "floor_id": "first_floor",
            "humidity_entity_id": "sensor.mock_humidity",
            "icon": "mdi:garage",
            "labels": ["label_1", "label_2"],
            "name": "mock 2",
            "picture": "/image/example.png",
            "temperature_entity_id": "sensor.mock_temperature",
        }
    )

    msg = await client.receive_json()

    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["alias_1", "alias_2"]),
            "area_id": area.id,
            "floor_id": "first_floor",
            "humidity_entity_id": "sensor.mock_humidity",
            "icon": "mdi:garage",
            "labels": unordered(["label_1", "label_2"]),
            "name": "mock 2",
            "picture": "/image/example.png",
            "temperature_entity_id": "sensor.mock_temperature",
            "created_at": created_at.timestamp(),
            "modified_at": modified_at.timestamp(),
        }
    )
    expect(len(area_registry.areas)).to_equal(1)

    modified_at = datetime.fromisoformat("2024-07-16T13:50:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/update",
            "aliases": ["alias_1", "alias_1"],
            "area_id": area.id,
            "floor_id": None,
            "humidity_entity_id": None,
            "icon": None,
            "labels": [],
            "picture": None,
            "temperature_entity_id": None,
        }
    )

    msg = await client.receive_json()

    expect(msg["result"]).to_equal(
        {
            "aliases": ["alias_1"],
            "area_id": area.id,
            "floor_id": None,
            "icon": None,
            "labels": [],
            "name": "mock 2",
            "picture": None,
            "temperature_entity_id": None,
            "humidity_entity_id": None,
            "created_at": created_at.timestamp(),
            "modified_at": modified_at.timestamp(),
        }
    )
    expect(len(area_registry.areas)).to_equal(1)

    modified_at = datetime.fromisoformat("2024-07-16T13:55:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/update",
            "aliases": ["alias_1", "", " ", " alias_2 "],
            "area_id": area.id,
            "floor_id": None,
            "humidity_entity_id": None,
            "icon": None,
            "labels": [],
            "picture": None,
            "temperature_entity_id": None,
        }
    )

    msg = await client.receive_json()

    expect(msg["result"]).to_equal(
        {
            "aliases": unordered(["alias_1", "alias_2"]),
            "area_id": area.id,
            "floor_id": None,
            "icon": None,
            "labels": [],
            "name": "mock 2",
            "picture": None,
            "temperature_entity_id": None,
            "humidity_entity_id": None,
            "created_at": created_at.timestamp(),
            "modified_at": modified_at.timestamp(),
        }
    )
    expect(len(area_registry.areas)).to_equal(1)


@test
async def update_area_with_same_name(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test update entry."""
    area = area_registry.async_create("mock 1")

    await client.send_json_auto_id(
        {
            "area_id": area.id,
            "name": "mock 1",
            "type": "config/area_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(msg["result"]["area_id"]).to_equal(area.id)
    expect(msg["result"]["name"]).to_equal("mock 1")
    expect(len(area_registry.areas)).to_equal(1)


@test
async def update_area_with_name_already_in_use(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test update entry."""
    area = area_registry.async_create("mock 1")
    area_registry.async_create("mock 2")

    await client.send_json_auto_id(
        {
            "area_id": area.id,
            "name": "mock 2",
            "type": "config/area_registry/update",
        }
    )

    msg = await client.receive_json()

    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_info")
    expect(msg["error"]["message"]).to_equal(
        "The name mock 2 (mock2) is already in use"
    )
    expect(len(area_registry.areas)).to_equal(2)


@test
async def reorder_areas(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test reorder areas."""
    area1 = area_registry.async_create("mock 1")
    area2 = area_registry.async_create("mock 2")
    area3 = area_registry.async_create("mock 3")

    await client.send_json_auto_id({"type": "config/area_registry/list"})
    msg = await client.receive_json()
    expect([area["area_id"] for area in msg["result"]]).to_equal(
        [area1.id, area2.id, area3.id]
    )

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/reorder",
            "area_ids": [area3.id, area1.id, area2.id],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    await client.send_json_auto_id({"type": "config/area_registry/list"})
    msg = await client.receive_json()
    expect([area["area_id"] for area in msg["result"]]).to_equal(
        [area3.id, area1.id, area2.id]
    )


@test
async def reorder_areas_invalid_area_ids(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test reorder with invalid area IDs."""
    area1 = area_registry.async_create("mock 1")
    area_registry.async_create("mock 2")

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/reorder",
            "area_ids": [area1.id],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_format")
    expect("must contain all existing area IDs" in msg["error"]["message"]).to_be(True)


@test
async def reorder_areas_with_nonexistent_id(
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
) -> None:
    """Test reorder with nonexistent area ID."""
    area1 = area_registry.async_create("mock 1")
    area2 = area_registry.async_create("mock 2")

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/reorder",
            "area_ids": [area1.id, area2.id, "nonexistent"],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(False)
    expect(msg["error"]["code"]).to_equal("invalid_format")


@test
async def reorder_areas_persistence(
    hass: HomeAssistant = Depends(hass_fixture),
    client: MockHAClientWebSocket = Depends(area_registry_client_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
    hass_storage: dict[str, Any] = Depends(hass_storage_fx),
) -> None:
    """Test that area reordering is persisted."""
    del hass_storage
    area1 = area_registry.async_create("mock 1")
    area2 = area_registry.async_create("mock 2")
    area3 = area_registry.async_create("mock 3")

    await client.send_json_auto_id(
        {
            "type": "config/area_registry/reorder",
            "area_ids": [area2.id, area3.id, area1.id],
        }
    )
    msg = await client.receive_json()
    expect(msg["success"]).to_be(True)

    await hass.async_block_till_done()

    area_ids = [area.id for area in area_registry.async_list_areas()]
    expect(area_ids).to_equal([area2.id, area3.id, area1.id])
