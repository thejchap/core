"""Tests for the floor registry."""

from datetime import UTC, datetime
from functools import partial
import re
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, floor_registry as fr
from homeassistant.util.dt import utcnow

from tests.common import async_capture_events, flush_store
from tests.hass_fixtures import (
    area_registry,
    floor_registry,
    freezer,
    hass,
    hass_storage,
    hass_unloaded,
)


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


async def _assert_thread_check_raises(coro_factory, method_name: str) -> None:
    """Verify coro_factory raises RuntimeError about cross-thread use."""
    try:
        await coro_factory()
    except RuntimeError as err:
        expect(str(err)).to_contain(
            f"Detected code that calls floor_registry.{method_name} from a thread"
        )
        return
    raise AssertionError("Expected RuntimeError")


@test
async def list_floors(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can read floors."""
    floors = floor_registry.async_list_floors()
    expect(len(list(floors))).to_equal(len(floor_registry.floors))


@test
async def create_floor(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can create floors."""
    del freezer
    update_events = async_capture_events(hass, fr.EVENT_FLOOR_REGISTRY_UPDATED)
    floor = floor_registry.async_create(
        name="First floor",
        icon="mdi:home-floor-1",
        aliases={"first", "ground", "ground floor"},
        level=1,
    )

    expect(floor).to_equal(
        fr.FloorEntry(
            floor_id="first_floor",
            name="First floor",
            icon="mdi:home-floor-1",
            aliases={"first", "ground", "ground floor"},
            level=1,
            created_at=utcnow(),
            modified_at=utcnow(),
        )
    )

    expect(len(floor_registry.floors)).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "floor_id": floor.floor_id,
        }
    )


@test
async def create_floor_with_name_already_in_use(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can't create a floor with a name already in use."""
    update_events = async_capture_events(hass, fr.EVENT_FLOOR_REGISTRY_UPDATED)
    floor_registry.async_create("First floor")

    expect(lambda: floor_registry.async_create("First floor")).to_raise(
        ValueError,
        match=re.escape("The name First floor (firstfloor) is already in use"),
    )

    await hass.async_block_till_done()

    expect(len(floor_registry.floors)).to_equal(1)
    expect(len(update_events)).to_equal(1)


@test
async def create_floor_with_id_already_in_use(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can't create an floor with an id already in use."""
    floor = floor_registry.async_create("First")

    updated_floor = floor_registry.async_update(floor.floor_id, name="Second")
    expect(updated_floor.floor_id).to_equal(floor.floor_id)

    another_floor = floor_registry.async_create("First")
    expect(floor.floor_id).not_.to_equal(another_floor.floor_id)
    expect(another_floor.floor_id).to_equal("first_2")


@test
async def delete_floor(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can delete a floor."""
    update_events = async_capture_events(hass, fr.EVENT_FLOOR_REGISTRY_UPDATED)
    floor = floor_registry.async_create("First floor")
    expect(len(floor_registry.floors)).to_equal(1)

    floor_registry.async_delete(floor.floor_id)

    expect(bool(floor_registry.floors)).to_be(False)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "floor_id": floor.floor_id,
        }
    )
    expect(update_events[1].data).to_equal(
        {
            "action": "remove",
            "floor_id": floor.floor_id,
        }
    )


@test
async def delete_non_existing_floor(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can't delete a floor that doesn't exist."""
    floor_registry.async_create("First floor")

    expect(lambda: floor_registry.async_delete("")).to_raise(KeyError)

    expect(len(floor_registry.floors)).to_equal(1)


@test
async def update_floor(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can update floors."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)

    update_events = async_capture_events(hass, fr.EVENT_FLOOR_REGISTRY_UPDATED)
    floor = floor_registry.async_create("First floor")

    expect(floor).to_equal(
        fr.FloorEntry(
            floor_id="first_floor",
            name="First floor",
            icon=None,
            aliases=set(),
            level=None,
            created_at=created_at,
            modified_at=created_at,
        )
    )
    expect(len(floor_registry.floors)).to_equal(1)

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)

    updated_floor = floor_registry.async_update(
        floor.floor_id,
        name="Second floor",
        icon="mdi:home-floor-2",
        aliases={"ground", "downstairs"},
        level=2,
    )

    expect(updated_floor).not_.to_equal(floor)
    expect(updated_floor).to_equal(
        fr.FloorEntry(
            floor_id="first_floor",
            name="Second floor",
            icon="mdi:home-floor-2",
            aliases={"ground", "downstairs"},
            level=2,
            created_at=created_at,
            modified_at=modified_at,
        )
    )

    expect(len(floor_registry.floors)).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "floor_id": floor.floor_id,
        }
    )
    expect(update_events[1].data).to_equal(
        {
            "action": "update",
            "floor_id": floor.floor_id,
        }
    )


@test
async def update_floor_with_same_data(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can reapply the same data to a floor and it won't update."""
    update_events = async_capture_events(hass, fr.EVENT_FLOOR_REGISTRY_UPDATED)
    floor = floor_registry.async_create(
        "First floor",
        icon="mdi:home-floor-1",
    )

    updated_floor = floor_registry.async_update(
        floor_id=floor.floor_id,
        name="First floor",
        icon="mdi:home-floor-1",
    )
    expect(floor).to_equal(updated_floor)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "floor_id": floor.floor_id,
        }
    )


@test
async def update_floor_with_same_name_change_case(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can reapply the same name with a different case to a floor."""
    floor = floor_registry.async_create("first floor")

    updated_floor = floor_registry.async_update(floor.floor_id, name="First floor")

    expect(updated_floor.floor_id).to_equal(floor.floor_id)
    expect(updated_floor.name).to_equal("First floor")
    expect(updated_floor.normalized_name).to_equal(floor.normalized_name)
    expect(len(floor_registry.floors)).to_equal(1)


@test
async def update_floor_with_name_already_in_use(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can't update a floor with a name already in use."""
    floor1 = floor_registry.async_create("First floor")
    floor2 = floor_registry.async_create("Second floor")

    expect(
        lambda: floor_registry.async_update(floor1.floor_id, name="Second floor")
    ).to_raise(
        ValueError,
        match=re.escape("The name Second floor (secondfloor) is already in use"),
    )

    expect(floor1.name).to_equal("First floor")
    expect(floor2.name).to_equal("Second floor")
    expect(len(floor_registry.floors)).to_equal(2)


@test
async def update_floor_with_normalized_name_already_in_use(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure that we can't update a floor with a normalized name already in use."""
    floor1 = floor_registry.async_create("first")
    floor2 = floor_registry.async_create("S E C O N D")

    expect(
        lambda: floor_registry.async_update(floor1.floor_id, name="second")
    ).to_raise(
        ValueError,
        match=re.escape("The name second (second) is already in use"),
    )

    expect(floor1.name).to_equal("first")
    expect(floor2.name).to_equal("S E C O N D")
    expect(len(floor_registry.floors)).to_equal(2)


@test
async def load_floors(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can load/save data correctly."""
    floor1_created = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    freezer.move_to(floor1_created)
    floor1 = floor_registry.async_create(
        "First floor",
        icon="mdi:home-floor-1",
        aliases={"first", "ground"},
        level=1,
    )

    floor2_created = datetime.fromisoformat("2024-02-01T00:00:00+00:00")
    freezer.move_to(floor2_created)
    floor2 = floor_registry.async_create(
        "Second floor",
        icon="mdi:home-floor-2",
        aliases={"first", "ground"},
        level=2,
    )

    expect(len(floor_registry.floors)).to_equal(2)

    registry2 = fr.FloorRegistry(hass)
    await flush_store(floor_registry._store)
    await registry2.async_load()

    expect(len(registry2.floors)).to_equal(2)
    expect(list(floor_registry.floors)).to_equal(list(registry2.floors))

    floor1_registry2 = registry2.async_get_floor_by_name("First floor")
    expect(floor1_registry2).to_equal(floor1)

    floor2_registry2 = registry2.async_get_floor_by_name("Second floor")
    expect(floor2_registry2).to_equal(floor2)


@test
async def loading_floors_from_storage(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading stored floors on start."""
    hass_storage[fr.STORAGE_KEY] = {
        "version": fr.STORAGE_VERSION_MAJOR,
        "data": {
            "floors": [
                {
                    "icon": "mdi:home-floor-1",
                    "floor_id": "first_floor",
                    "name": "First floor",
                    "aliases": ["first", "ground"],
                    "level": 1,
                }
            ]
        },
    }

    await fr.async_load(hass)
    registry = fr.async_get(hass)

    expect(len(registry.floors)).to_equal(1)


@test
async def getting_floor_by_name(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure we can get the floors by name."""
    floor = floor_registry.async_create("First floor")
    floor2 = floor_registry.async_get_floor_by_name("first floor")
    floor3 = floor_registry.async_get_floor_by_name("first    floor")

    expect(floor).to_equal(floor2)
    expect(floor).to_equal(floor3)
    expect(floor2).to_equal(floor3)

    get_floor = floor_registry.async_get_floor(floor.floor_id)
    expect(get_floor).to_equal(floor)


@test
async def async_get_floors_by_alias(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure we can get the floors by alias."""
    floor1 = floor_registry.async_create("First floor", aliases=("alias_1", "alias_2"))
    floor2 = floor_registry.async_create("Second floor", aliases=("alias_1", "alias_3"))

    expect(floor_registry.async_get_floors_by_alias("A l i a s_1")).to_equal(
        [floor1, floor2]
    )
    expect(floor_registry.async_get_floors_by_alias("A l i a s_2")).to_equal([floor1])
    expect(floor_registry.async_get_floors_by_alias("A l i a s_3")).to_equal([floor2])


@test
async def async_get_floors_by_alias_collisions(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure we can get the floors by alias when the aliases have collisions."""
    floor = floor_registry.async_create("First floor")
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal([])

    updated_floor = floor_registry.async_update(floor.floor_id, aliases={"alias1"})
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal(
        [updated_floor]
    )

    updated_floor = floor_registry.async_update(
        floor.floor_id, aliases={"alias1", "alias  1"}
    )
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal(
        [updated_floor]
    )

    updated_floor = floor_registry.async_update(
        floor.floor_id, aliases={"alias1", "alias 1", "alias  1"}
    )
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal(
        [updated_floor]
    )

    updated_floor = floor_registry.async_update(
        floor.floor_id, aliases={"alias1", "alias  1"}
    )
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal(
        [updated_floor]
    )

    updated_floor = floor_registry.async_update(floor.floor_id, aliases={"alias1"})
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal(
        [updated_floor]
    )

    updated_floor = floor_registry.async_update(floor.floor_id, aliases={})
    expect(floor_registry.async_get_floors_by_alias("A l i a s 1")).to_equal([])


@test
async def async_get_floor_by_name_not_found(
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Make sure we return None for non-existent floors."""
    floor_registry.async_create("First floor")

    expect(len(floor_registry.floors)).to_equal(1)

    expect(floor_registry.async_get_floor_by_name("non_exist")).to_be_none()


@test
async def floor_removed_from_areas(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Test if floor gets removed from areas when the floor is removed."""
    floor = floor_registry.async_create("First floor")
    expect(len(floor_registry.floors)).to_equal(1)

    entry = area_registry.async_create(name="Kitchen")
    area_registry.async_update(entry.id, floor_id=floor.floor_id)

    entries = ar.async_entries_for_floor(area_registry, floor.floor_id)
    expect(len(entries)).to_equal(1)

    floor_registry.async_delete(floor.floor_id)
    await hass.async_block_till_done()

    entries = ar.async_entries_for_floor(area_registry, floor.floor_id)
    expect(len(entries)).to_equal(0)


@test
async def async_create_thread_safety(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Test async_create raises when called from wrong thread."""
    await _assert_thread_check_raises(
        lambda: hass.async_add_executor_job(floor_registry.async_create, "any"),
        "async_create",
    )


@test
async def async_delete_thread_safety(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Test async_delete raises when called from wrong thread."""
    any_floor = floor_registry.async_create("any")

    await _assert_thread_check_raises(
        lambda: hass.async_add_executor_job(floor_registry.async_delete, any_floor),
        "async_delete",
    )


@test
async def async_update_thread_safety(
    hass: HomeAssistant = Depends(hass),
    floor_registry: fr.FloorRegistry = Depends(floor_registry),
) -> None:
    """Test async_update raises when called from wrong thread."""
    any_floor = floor_registry.async_create("any")

    await _assert_thread_check_raises(
        lambda: hass.async_add_executor_job(
            partial(floor_registry.async_update, any_floor.floor_id, name="new name")
        ),
        "async_update",
    )


@test
async def migration_from_1_1(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migration from version 1.1."""
    hass_storage[fr.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "floors": [
                {
                    "floor_id": "12345A",
                    "name": "AA floor no level floor",
                    "aliases": [],
                    "icon": None,
                    "level": None,
                },
                {
                    "floor_id": "12345B",
                    "name": "CC floor no level floor",
                    "aliases": [],
                    "icon": None,
                    "level": None,
                },
                {
                    "floor_id": "12345C",
                    "name": "bb floor no level floor",
                    "aliases": [],
                    "icon": None,
                    "level": None,
                },
                {
                    "floor_id": "12345D",
                    "name": "AA floor level -1",
                    "aliases": [],
                    "icon": None,
                    "level": -1,
                },
                {
                    "floor_id": "12345E",
                    "name": "CC floor level -1",
                    "aliases": [],
                    "icon": None,
                    "level": -1,
                },
                {
                    "floor_id": "12345F",
                    "name": "bb floor level -1",
                    "aliases": [],
                    "icon": None,
                    "level": -1,
                },
                {
                    "floor_id": "12345G",
                    "name": "AA floor level 0",
                    "aliases": [],
                    "icon": None,
                    "level": 0,
                },
                {
                    "floor_id": "12345H",
                    "name": "CC floor level 0",
                    "aliases": [],
                    "icon": None,
                    "level": 0,
                },
                {
                    "floor_id": "12345I",
                    "name": "bb floor level 0",
                    "aliases": [],
                    "icon": None,
                    "level": 0,
                },
                {
                    "floor_id": "12345J",
                    "name": "AA floor level 1",
                    "aliases": [],
                    "icon": None,
                    "level": 1,
                },
                {
                    "floor_id": "12345K",
                    "name": "CC floor level 1",
                    "aliases": [],
                    "icon": None,
                    "level": 1,
                },
                {
                    "floor_id": "12345L",
                    "name": "bb floor level 1",
                    "aliases": [],
                    "icon": None,
                    "level": 1,
                },
            ]
        },
    }

    await fr.async_load(hass)
    registry = fr.async_get(hass)

    entry = registry.async_get_floor_by_name("AA floor no level floor")
    expect(entry.floor_id).to_equal("12345A")

    expect(list(registry.async_list_floors())).to_equal(
        [
            fr.FloorEntry(
                name="AA floor level 1",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345J",
                icon=None,
                level=1,
            ),
            fr.FloorEntry(
                name="bb floor level 1",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345L",
                icon=None,
                level=1,
            ),
            fr.FloorEntry(
                name="CC floor level 1",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345K",
                icon=None,
                level=1,
            ),
            fr.FloorEntry(
                name="AA floor level 0",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345G",
                icon=None,
                level=0,
            ),
            fr.FloorEntry(
                name="bb floor level 0",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345I",
                icon=None,
                level=0,
            ),
            fr.FloorEntry(
                name="CC floor level 0",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345H",
                icon=None,
                level=0,
            ),
            fr.FloorEntry(
                name="AA floor level -1",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345D",
                icon=None,
                level=-1,
            ),
            fr.FloorEntry(
                name="bb floor level -1",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345F",
                icon=None,
                level=-1,
            ),
            fr.FloorEntry(
                name="CC floor level -1",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345E",
                icon=None,
                level=-1,
            ),
            fr.FloorEntry(
                name="AA floor no level floor",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345A",
                icon=None,
                level=None,
            ),
            fr.FloorEntry(
                name="bb floor no level floor",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345C",
                icon=None,
                level=None,
            ),
            fr.FloorEntry(
                name="CC floor no level floor",
                created_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                modified_at=datetime(1970, 1, 1, 0, 0, tzinfo=UTC),
                aliases=set(),
                floor_id="12345B",
                icon=None,
                level=None,
            ),
        ]
    )

    await flush_store(registry._store)
    expect(hass_storage[fr.STORAGE_KEY]).to_equal(
        {
            "version": fr.STORAGE_VERSION_MAJOR,
            "minor_version": fr.STORAGE_VERSION_MINOR,
            "key": fr.STORAGE_KEY,
            "data": {
                "floors": [
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345J",
                        "icon": None,
                        "level": 1,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "AA floor level 1",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345L",
                        "icon": None,
                        "level": 1,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "bb floor level 1",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345K",
                        "icon": None,
                        "level": 1,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "CC floor level 1",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345G",
                        "icon": None,
                        "level": 0,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "AA floor level 0",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345I",
                        "icon": None,
                        "level": 0,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "bb floor level 0",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345H",
                        "icon": None,
                        "level": 0,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "CC floor level 0",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345D",
                        "icon": None,
                        "level": -1,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "AA floor level -1",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345F",
                        "icon": None,
                        "level": -1,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "bb floor level -1",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345E",
                        "icon": None,
                        "level": -1,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "CC floor level -1",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345A",
                        "icon": None,
                        "level": None,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "AA floor no level floor",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345C",
                        "icon": None,
                        "level": None,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "bb floor no level floor",
                    },
                    {
                        "aliases": [],
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "floor_id": "12345B",
                        "icon": None,
                        "level": None,
                        "modified_at": "1970-01-01T00:00:00+00:00",
                        "name": "CC floor no level floor",
                    },
                ]
            },
        }
    )
