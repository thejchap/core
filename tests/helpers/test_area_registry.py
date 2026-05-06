"""Tests for the Area Registry."""

from datetime import UTC, datetime, timedelta
from functools import partial
import re
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    floor_registry as fr,
    label_registry as lr,
)
from homeassistant.util.dt import utcnow

from tests.common import ANY, async_capture_events, flush_store
from tests.hass_fixtures import (
    area_registry,
    floor_registry,
    freezer,
    hass,
    hass_storage,
    hass_unloaded,
    label_registry,
)


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


def _install_mock_temperature_humidity_entity(hass: HomeAssistant) -> None:
    """Mock temperature and humidity sensors.

    Plain helper rather than an ``@fixture`` so it does not auto-apply
    to every test in the module (module-level Tryke fixtures do).
    """
    hass.states.async_set(
        "sensor.mock_temperature",
        "20",
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
            ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
        },
    )
    hass.states.async_set(
        "sensor.mock_humidity",
        "50",
        {
            ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
            ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
        },
    )


@test
async def list_areas(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can read areas."""
    area_registry.async_create("mock")

    areas = area_registry.async_list_areas()

    expect(len(areas)).to_equal(len(area_registry.areas))


@test
async def create_area(
    hass: HomeAssistant = Depends(hass),
    freezer: FrozenDateTimeFactory = Depends(freezer),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can create an area."""
    _install_mock_temperature_humidity_entity(hass)
    update_events = async_capture_events(hass, ar.EVENT_AREA_REGISTRY_UPDATED)

    # Create area with only mandatory parameters
    area = area_registry.async_create("mock")

    expect(area).to_equal(
        ar.AreaEntry(
            aliases=set(),
            floor_id=None,
            icon=None,
            id=ANY,
            labels=set(),
            name="mock",
            picture=None,
            created_at=utcnow(),
            modified_at=utcnow(),
            temperature_entity_id=None,
            humidity_entity_id=None,
        )
    )
    expect(len(area_registry.areas)).to_equal(1)

    freezer.tick(timedelta(minutes=5))

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[-1].data).to_equal(
        {"action": "create", "area_id": area.id}
    )

    # Create area with all parameters
    area2 = area_registry.async_create(
        "mock 2",
        aliases={"alias_1", "alias_2"},
        labels={"label1", "label2"},
        picture="/image/example.png",
        temperature_entity_id="sensor.mock_temperature",
        humidity_entity_id="sensor.mock_humidity",
    )

    expect(area2).to_equal(
        ar.AreaEntry(
            aliases={"alias_1", "alias_2"},
            floor_id=None,
            icon=None,
            id=ANY,
            labels={"label1", "label2"},
            name="mock 2",
            picture="/image/example.png",
            created_at=utcnow(),
            modified_at=utcnow(),
            temperature_entity_id="sensor.mock_temperature",
            humidity_entity_id="sensor.mock_humidity",
        )
    )
    expect(len(area_registry.areas)).to_equal(2)
    expect(area.created_at).not_.to_equal(area2.created_at)
    expect(area.modified_at).not_.to_equal(area2.modified_at)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[-1].data).to_equal(
        {"action": "create", "area_id": area2.id}
    )


@test
async def create_area_with_name_already_in_use(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can't create an area with a name already in use."""
    update_events = async_capture_events(hass, ar.EVENT_AREA_REGISTRY_UPDATED)
    area_registry.async_create("mock")

    expect(lambda: area_registry.async_create("mock")).to_raise(
        ValueError, match=r"The name mock \(mock\) is already in use"
    )

    await hass.async_block_till_done()

    expect(len(area_registry.areas)).to_equal(1)
    expect(len(update_events)).to_equal(1)


@test
async def create_area_with_id_already_in_use(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can't create an area with a name already in use."""
    area1 = area_registry.async_create("mock")

    updated_area1 = area_registry.async_update(area1.id, name="New Name")
    expect(updated_area1.id).to_equal(area1.id)

    area2 = area_registry.async_create("mock")
    expect(area2.id).to_equal("mock_2")


@test
async def delete_area(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can delete an area."""
    update_events = async_capture_events(hass, ar.EVENT_AREA_REGISTRY_UPDATED)
    area = area_registry.async_create("mock")

    area_registry.async_delete(area.id)

    expect(area_registry.areas).to_be_falsy()

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {"action": "create", "area_id": area.id}
    )
    expect(update_events[1].data).to_equal(
        {"action": "remove", "area_id": area.id}
    )


@test
async def delete_non_existing_area(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can't delete an area that doesn't exist."""
    area_registry.async_create("mock")

    expect(lambda: area_registry.async_delete("")).to_raise(KeyError)

    expect(len(area_registry.areas)).to_equal(1)


@test
async def update_area(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
    label_registry: lr.LabelRegistry = Depends(label_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can read areas."""
    _install_mock_temperature_humidity_entity(hass)
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)
    update_events = async_capture_events(hass, ar.EVENT_AREA_REGISTRY_UPDATED)
    floor_registry.async_create("first")
    area = area_registry.async_create("mock")
    expect(area.modified_at).to_equal(created_at)

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)

    updated_area = area_registry.async_update(
        area.id,
        aliases={"alias_1", "alias_2"},
        floor_id="first",
        icon="mdi:garage",
        labels={"label1", "label2"},
        name="mock1",
        picture="/image/example.png",
        temperature_entity_id="sensor.mock_temperature",
        humidity_entity_id="sensor.mock_humidity",
    )

    expect(updated_area).not_.to_equal(area)
    expect(updated_area).to_equal(
        ar.AreaEntry(
            aliases={"alias_1", "alias_2"},
            floor_id="first",
            icon="mdi:garage",
            id=ANY,
            labels={"label1", "label2"},
            name="mock1",
            picture="/image/example.png",
            created_at=created_at,
            modified_at=modified_at,
            temperature_entity_id="sensor.mock_temperature",
            humidity_entity_id="sensor.mock_humidity",
        )
    )
    expect(len(area_registry.areas)).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {"action": "create", "area_id": area.id}
    )
    expect(update_events[1].data).to_equal(
        {"action": "update", "area_id": area.id}
    )


@test
async def update_area_with_same_name(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can reapply the same name to the area."""
    area = area_registry.async_create("mock")

    updated_area = area_registry.async_update(area.id, name="mock")

    expect(updated_area).to_equal(area)
    expect(len(area_registry.areas)).to_equal(1)


@test
async def update_area_with_same_name_change_case(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can reapply the same name with a different case to the area."""
    area = area_registry.async_create("mock")

    updated_area = area_registry.async_update(area.id, name="Mock")

    expect(updated_area.name).to_equal("Mock")
    expect(updated_area.id).to_equal(area.id)
    expect(updated_area.normalized_name).to_equal(area.normalized_name)
    expect(len(area_registry.areas)).to_equal(1)


@test
async def update_area_with_name_already_in_use(
    area_registry: ar.AreaRegistry = Depends(area_registry),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can't update an area with a name already in use."""
    floor = floor_registry.async_create("mock")
    floor_id = floor.floor_id
    area1 = area_registry.async_create("mock1", floor_id=floor_id)
    area2 = area_registry.async_create("mock2")

    expect(
        lambda: area_registry.async_update(area1.id, name="mock2")
    ).to_raise(ValueError, match=r"The name mock2 \(mock2\) is already in use")

    expect(area1.name).to_equal("mock1")
    expect(area2.name).to_equal("mock2")
    expect(len(area_registry.areas)).to_equal(2)

    expect(area_registry.areas.get_areas_for_floor(floor_id)).to_equal([area1])


@test
async def update_area_with_normalized_name_already_in_use(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can't update an area with a normalized name already in use."""
    area1 = area_registry.async_create("mock1")
    area2 = area_registry.async_create("Moc k2")

    expect(
        lambda: area_registry.async_update(area1.id, name="mock2")
    ).to_raise(ValueError, match=r"The name mock2 \(mock2\) is already in use")

    expect(area1.name).to_equal("mock1")
    expect(area2.name).to_equal("Moc k2")
    expect(len(area_registry.areas)).to_equal(2)


@test.cases(
    test.case(
        "temperature_invalid_entity",
        create_kwargs={"temperature_entity_id": "sensor.invalid"},
        error_message="Entity sensor.invalid does not exist",
    ),
    test.case(
        "temperature_wrong_domain",
        create_kwargs={"temperature_entity_id": "light.kitchen"},
        error_message="Entity light.kitchen is not a temperature sensor",
    ),
    test.case(
        "temperature_wrong_class",
        create_kwargs={"temperature_entity_id": "sensor.random"},
        error_message="Entity sensor.random is not a temperature sensor",
    ),
    test.case(
        "humidity_invalid_entity",
        create_kwargs={"humidity_entity_id": "sensor.invalid"},
        error_message="Entity sensor.invalid does not exist",
    ),
    test.case(
        "humidity_wrong_domain",
        create_kwargs={"humidity_entity_id": "light.kitchen"},
        error_message="Entity light.kitchen is not a humidity sensor",
    ),
    test.case(
        "humidity_wrong_class",
        create_kwargs={"humidity_entity_id": "sensor.random"},
        error_message="Entity sensor.random is not a humidity sensor",
    ),
)
async def update_area_entity_validation(
    create_kwargs: dict[str, Any],
    error_message: str,
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can't update an area with an invalid entity."""
    _install_mock_temperature_humidity_entity(hass)
    area = area_registry.async_create("mock")
    hass.states.async_set("light.kitchen", "on", {})
    hass.states.async_set("sensor.random", "3", {})

    expect(
        lambda: area_registry.async_update(area.id, **create_kwargs)
    ).to_raise(ValueError, match=re.escape(error_message))

    expect(area.temperature_entity_id).to_be_none()
    expect(area.humidity_entity_id).to_be_none()


@test
async def load_area(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure that we can load/save data correctly."""
    area1 = area_registry.async_create("mock1")
    area2 = area_registry.async_create("mock2")

    expect(len(area_registry.areas)).to_equal(2)

    registry2 = ar.AreaRegistry(hass)
    await flush_store(area_registry._store)
    await registry2.async_load()

    expect(list(area_registry.areas)).to_equal(list(registry2.areas))

    area1_registry2 = registry2.async_get_or_create("mock1")
    expect(area1_registry2.id).to_equal(area1.id)
    area2_registry2 = registry2.async_get_or_create("mock2")
    expect(area2_registry2.id).to_equal(area2.id)


@test
async def loading_area_from_storage(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading stored areas on start."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    hass_storage[ar.STORAGE_KEY] = {
        "version": ar.STORAGE_VERSION_MAJOR,
        "minor_version": ar.STORAGE_VERSION_MINOR,
        "data": {
            "areas": [
                {
                    "aliases": ["alias_1", "alias_2"],
                    "floor_id": "first_floor",
                    "id": "12345A",
                    "icon": "mdi:garage",
                    "labels": ["mock-label1", "mock-label2"],
                    "name": "mock",
                    "picture": "blah",
                    "created_at": created_at.isoformat(),
                    "modified_at": modified_at.isoformat(),
                    "temperature_entity_id": "sensor.mock_temperature",
                    "humidity_entity_id": "sensor.mock_humidity",
                }
            ]
        },
    }

    await ar.async_load(hass)
    registry = ar.async_get(hass)

    expect(len(registry.areas)).to_equal(1)
    area = registry.areas["12345A"]
    expect(area).to_equal(
        ar.AreaEntry(
            aliases={"alias_1", "alias_2"},
            floor_id="first_floor",
            icon="mdi:garage",
            id="12345A",
            labels={"mock-label1", "mock-label2"},
            name="mock",
            picture="blah",
            created_at=created_at,
            modified_at=modified_at,
            temperature_entity_id="sensor.mock_temperature",
            humidity_entity_id="sensor.mock_humidity",
        )
    )


@test
async def migration_from_1_1(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migration from version 1.1."""
    hass_storage[ar.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "areas": [
                {"id": "12345A", "name": "AAA"},
                {"id": "12345B", "name": "CCC"},
                {"id": "12345C", "name": "bbb"},
            ]
        },
    }

    await ar.async_load(hass)
    registry = ar.async_get(hass)

    # Test data was loaded
    entry = registry.async_get_or_create("AAA")
    expect(entry.id).to_equal("12345A")

    # Check sort order
    expect(list(registry.async_list_areas())).to_equal(
        [
            ar.AreaEntry(
                name="AAA",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id=None,
                humidity_entity_id=None,
                icon=None,
                id="12345A",
                labels=set(),
                picture=None,
                temperature_entity_id=None,
            ),
            ar.AreaEntry(
                name="bbb",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id=None,
                humidity_entity_id=None,
                icon=None,
                id="12345C",
                labels=set(),
                picture=None,
                temperature_entity_id=None,
            ),
            ar.AreaEntry(
                name="CCC",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id=None,
                humidity_entity_id=None,
                icon=None,
                id="12345B",
                labels=set(),
                picture=None,
                temperature_entity_id=None,
            ),
        ]
    )

    # Check we store migrated data
    await flush_store(registry._store)
    expect(hass_storage[ar.STORAGE_KEY]).to_equal(
        {
            "version": ar.STORAGE_VERSION_MAJOR,
            "minor_version": ar.STORAGE_VERSION_MINOR,
            "key": ar.STORAGE_KEY,
            "data": {
                "areas": [
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": None,
                        "humidity_entity_id": None,
                        "icon": None,
                        "id": "12345A",
                        "labels": [],
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "AAA",
                        "picture": None,
                        "temperature_entity_id": None,
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": None,
                        "humidity_entity_id": None,
                        "icon": None,
                        "id": "12345C",
                        "labels": [],
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "bbb",
                        "picture": None,
                        "temperature_entity_id": None,
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": None,
                        "humidity_entity_id": None,
                        "icon": None,
                        "id": "12345B",
                        "labels": [],
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "CCC",
                        "picture": None,
                        "temperature_entity_id": None,
                    },
                ]
            },
        }
    )


@test
async def async_get_or_create(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure we can get the area by name."""
    area = area_registry.async_get_or_create("Mock1")
    area2 = area_registry.async_get_or_create("mock1")
    area3 = area_registry.async_get_or_create("mock   1")

    expect(area).to_equal(area2)
    expect(area).to_equal(area3)
    expect(area2).to_equal(area3)


@test
async def async_get_area_by_name(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure we can get the area by name."""
    area_registry.async_create("Mock1")

    expect(len(area_registry.areas)).to_equal(1)

    expect(
        area_registry.async_get_area_by_name("M o c k 1").normalized_name
    ).to_equal("mock1")


@test
async def async_get_areas_by_alias(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure we can get the areas by alias."""
    area1 = area_registry.async_create("Mock1", aliases=("alias_1", "alias_2"))
    area2 = area_registry.async_create("Mock2", aliases=("alias_1", "alias_3"))

    expect(len(area_registry.areas)).to_equal(2)

    expect(area_registry.async_get_areas_by_alias("A l i a s_1")).to_equal(
        [area1, area2]
    )
    expect(area_registry.async_get_areas_by_alias("A l i a s_2")).to_equal([area1])
    expect(area_registry.async_get_areas_by_alias("A l i a s_3")).to_be_truthy()


@test
async def async_get_areas_by_alias_collisions(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure we can get the areas by alias when the aliases have collisions."""
    area = area_registry.async_create("Mock1")
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal([])

    # Add an alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1"})
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal(
        [updated_area]
    )

    # Add a colliding alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1", "alias  1"})
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal(
        [updated_area]
    )

    # Add a colliding alias
    updated_area = area_registry.async_update(
        area.id, aliases={"alias1", "alias 1", "alias  1"}
    )
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal(
        [updated_area]
    )

    # Remove a colliding alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1", "alias  1"})
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal(
        [updated_area]
    )

    # Remove a colliding alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1"})
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal(
        [updated_area]
    )

    # Remove all aliases
    updated_area = area_registry.async_update(area.id, aliases={})
    expect(area_registry.async_get_areas_by_alias("A l i a s 1")).to_equal([])


@test
async def async_get_area_by_name_not_found(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure we return None for non-existent areas."""
    area_registry.async_create("Mock1")

    expect(len(area_registry.areas)).to_equal(1)

    expect(area_registry.async_get_area_by_name("non_exist")).to_be_none()


@test
async def async_get_area(
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """Make sure we can get the area by id."""
    area = area_registry.async_create("Mock1")

    expect(len(area_registry.areas)).to_equal(1)

    expect(area_registry.async_get_area(area.id).normalized_name).to_equal("mock1")


@test
async def removing_floors(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure we can clear floors."""
    first_floor = floor_registry.async_create("First floor")
    second_floor = floor_registry.async_create("Second floor")

    kitchen = area_registry.async_create("Kitchen")
    kitchen = area_registry.async_update(kitchen.id, floor_id=first_floor.floor_id)
    bedroom = area_registry.async_create("Bedroom")
    bedroom = area_registry.async_update(bedroom.id, floor_id=second_floor.floor_id)

    floor_registry.async_delete(first_floor.floor_id)
    await hass.async_block_till_done()
    expect(area_registry.async_get_area(kitchen.id).floor_id).to_be_none()
    expect(area_registry.async_get_area(bedroom.id).floor_id).to_equal(
        second_floor.floor_id
    )

    floor_registry.async_delete(second_floor.floor_id)
    await hass.async_block_till_done()
    expect(area_registry.async_get_area(kitchen.id).floor_id).to_be_none()
    expect(area_registry.async_get_area(bedroom.id).floor_id).to_be_none()


@test
async def entries_for_floor(
    area_registry: ar.AreaRegistry = Depends(area_registry),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Test getting area entries by floor."""
    first_floor = floor_registry.async_create("First floor")
    second_floor = floor_registry.async_create("Second floor")

    kitchen = area_registry.async_create("Kitchen")
    kitchen = area_registry.async_update(kitchen.id, floor_id=first_floor.floor_id)
    living_room = area_registry.async_create("Living room")
    living_room = area_registry.async_update(
        living_room.id, floor_id=first_floor.floor_id
    )
    bedroom = area_registry.async_create("Bedroom")
    bedroom = area_registry.async_update(bedroom.id, floor_id=second_floor.floor_id)

    entries = ar.async_entries_for_floor(area_registry, first_floor.floor_id)
    expect(len(entries)).to_equal(2)
    expect(entries).to_equal([kitchen, living_room])

    entries = ar.async_entries_for_floor(area_registry, second_floor.floor_id)
    expect(len(entries)).to_equal(1)
    expect(entries).to_equal([bedroom])

    expect(ar.async_entries_for_floor(area_registry, "unknown")).to_be_falsy()
    expect(ar.async_entries_for_floor(area_registry, "")).to_be_falsy()


@test
async def removing_labels(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure we can clear labels."""
    label1 = label_registry.async_create("Label 1")
    label2 = label_registry.async_create("Label 2")

    kitchen = area_registry.async_create("Kitchen")
    kitchen = area_registry.async_update(
        kitchen.id, labels={label1.label_id, label2.label_id}
    )

    bedroom = area_registry.async_create("Bedroom")
    bedroom = area_registry.async_update(bedroom.id, labels={label2.label_id})

    expect(area_registry.async_get_area(kitchen.id).labels).to_equal(
        {label1.label_id, label2.label_id}
    )
    expect(area_registry.async_get_area(bedroom.id).labels).to_equal(
        {label2.label_id}
    )

    label_registry.async_delete(label1.label_id)
    await hass.async_block_till_done()

    expect(area_registry.async_get_area(kitchen.id).labels).to_equal(
        {label2.label_id}
    )
    expect(area_registry.async_get_area(bedroom.id).labels).to_equal(
        {label2.label_id}
    )

    label_registry.async_delete(label2.label_id)
    await hass.async_block_till_done()

    expect(area_registry.async_get_area(kitchen.id).labels).to_be_falsy()
    expect(area_registry.async_get_area(bedroom.id).labels).to_be_falsy()


@test
async def entries_for_label(
    area_registry: ar.AreaRegistry = Depends(area_registry),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Test getting area entries by label."""
    label1 = label_registry.async_create("Label 1")
    label2 = label_registry.async_create("Label 2")

    kitchen = area_registry.async_create("Kitchen")
    kitchen = area_registry.async_update(
        kitchen.id, labels={label1.label_id, label2.label_id}
    )
    living_room = area_registry.async_create("Living room")
    living_room = area_registry.async_update(living_room.id, labels={label1.label_id})
    bedroom = area_registry.async_create("Bedroom")
    bedroom = area_registry.async_update(bedroom.id, labels={label2.label_id})

    entries = ar.async_entries_for_label(area_registry, label1.label_id)
    expect(len(entries)).to_equal(2)
    expect(entries).to_equal([kitchen, living_room])

    entries = ar.async_entries_for_label(area_registry, label2.label_id)
    expect(len(entries)).to_equal(2)
    expect(entries).to_equal([kitchen, bedroom])

    expect(ar.async_entries_for_label(area_registry, "unknown")).to_be_falsy()
    expect(ar.async_entries_for_label(area_registry, "")).to_be_falsy()


@test
async def async_get_or_create_thread_checks(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """We raise when trying to create in the wrong thread."""
    await _assert_thread_check_raises(
        lambda: hass.async_add_executor_job(area_registry.async_create, "Mock1"),
        "async_create",
    )


@test
async def async_update_thread_checks(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """We raise when trying to update in the wrong thread."""
    area = area_registry.async_create("Mock1")
    await _assert_thread_check_raises(
        lambda: hass.async_add_executor_job(
            partial(area_registry.async_update, area.id, name="Mock2")
        ),
        "async_update",
    )


@test
async def async_delete_thread_checks(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
) -> None:
    """We raise when trying to delete in the wrong thread."""
    area = area_registry.async_create("Mock1")
    await _assert_thread_check_raises(
        lambda: hass.async_add_executor_job(area_registry.async_delete, area.id),
        "async_delete",
    )


async def _assert_thread_check_raises(coro_factory, method_name: str) -> None:
    """Assert the awaitable raises the registry thread-check RuntimeError."""
    try:
        await coro_factory()
    except RuntimeError as err:
        expect(str(err)).to_contain(
            f"Detected code that calls area_registry.{method_name} from a thread"
        )
        return
    raise AssertionError("Expected RuntimeError")
