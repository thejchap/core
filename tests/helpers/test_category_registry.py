"""Tests for the category registry."""

from datetime import datetime
from functools import partial
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import category_registry as cr
from homeassistant.util.dt import UTC

from tests.common import async_capture_events, flush_store
from tests.hass_fixtures import (
    category_registry,
    freezer,
    hass,
    hass_storage,
    hass_unloaded,
)


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def list_categories_for_scope(
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can read categories for scope."""
    categories = category_registry.async_list_categories(scope="automation")
    expect(len(list(categories))).to_equal(
        len(category_registry.categories.get("automation", {}))
    )


@test
async def create_category(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can create new categories."""
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    expect(bool(category.category_id)).to_be(True)
    expect(category.name).to_equal("Energy saving")
    expect(category.icon).to_equal("mdi:leaf")

    expect(len(category_registry.categories)).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "scope": "automation",
            "category_id": category.category_id,
        }
    )


@test
async def create_category_with_name_already_in_use(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can't create a category with the same name within a scope."""
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    expect(
        lambda: category_registry.async_create(
            scope="automation",
            name="ENERGY SAVING",
            icon="mdi:leaf",
        )
    ).to_raise(ValueError, match=r"The name 'ENERGY SAVING' is already in use")

    await hass.async_block_till_done()

    expect(len(category_registry.categories["automation"])).to_equal(1)
    expect(len(update_events)).to_equal(1)


@test
async def create_category_with_duplicate_name_in_other_scopes(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make we can create the same category in multiple scopes."""
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    category_registry.async_create(
        scope="script",
        name="Energy saving",
        icon="mdi:leaf",
    )

    await hass.async_block_till_done()

    expect(len(category_registry.categories["script"])).to_equal(1)
    expect(len(category_registry.categories["automation"])).to_equal(1)
    expect(len(update_events)).to_equal(2)


@test
async def delete_category(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can delete a category."""
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    expect(len(category_registry.categories["automation"])).to_equal(1)

    category_registry.async_delete(
        scope="automation", category_id=category.category_id
    )

    expect(bool(category_registry.categories["automation"])).to_be(False)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "scope": "automation",
            "category_id": category.category_id,
        }
    )
    expect(update_events[1].data).to_equal(
        {
            "action": "remove",
            "scope": "automation",
            "category_id": category.category_id,
        }
    )


@test
async def delete_non_existing_category(
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can't delete a category that doesn't exist."""
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    expect(
        lambda: category_registry.async_delete(scope="automation", category_id="")
    ).to_raise(KeyError)

    expect(
        lambda: category_registry.async_delete(
            scope="", category_id=category.category_id
        )
    ).to_raise(KeyError)

    expect(len(category_registry.categories["automation"])).to_equal(1)


@test
async def update_category(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can update categories."""
    created = datetime(2024, 2, 14, 12, 0, 0, tzinfo=UTC)
    freezer.move_to(created)
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )

    expect(len(category_registry.categories["automation"])).to_equal(1)
    expect(category).to_equal(
        cr.CategoryEntry(
            category_id=category.category_id,
            created_at=created,
            modified_at=created,
            name="Energy saving",
            icon=None,
        )
    )

    modified = datetime(2024, 3, 14, 12, 0, 0, tzinfo=UTC)
    freezer.move_to(modified)

    updated_category = category_registry.async_update(
        scope="automation",
        category_id=category.category_id,
        name="ENERGY SAVING",
        icon="mdi:leaf",
    )

    expect(updated_category != category).to_be(True)
    expect(updated_category).to_equal(
        cr.CategoryEntry(
            category_id=category.category_id,
            created_at=created,
            modified_at=modified,
            name="ENERGY SAVING",
            icon="mdi:leaf",
        )
    )

    expect(len(category_registry.categories["automation"])).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "scope": "automation",
            "category_id": category.category_id,
        }
    )
    expect(update_events[1].data).to_equal(
        {
            "action": "update",
            "scope": "automation",
            "category_id": category.category_id,
        }
    )


@test
async def update_category_with_same_data(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can reapply the same data to a category and it won't update."""
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    updated_category = category_registry.async_update(
        scope="automation",
        category_id=category.category_id,
        name="Energy saving",
        icon="mdi:leaf",
    )
    expect(category).to_equal(updated_category)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[0].data).to_equal(
        {
            "action": "create",
            "scope": "automation",
            "category_id": category.category_id,
        }
    )


@test
async def update_category_with_same_name_change_case(
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can reapply the same name with a different case to a category."""
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    updated_category = category_registry.async_update(
        scope="automation",
        category_id=category.category_id,
        name="ENERGY SAVING",
    )

    expect(updated_category.category_id).to_equal(category.category_id)
    expect(updated_category.name).to_equal("ENERGY SAVING")
    expect(updated_category.icon).to_equal("mdi:leaf")
    expect(len(category_registry.categories["automation"])).to_equal(1)


@test
async def update_category_with_name_already_in_use(
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can't update a category with a name already in use."""
    category1 = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    category2 = category_registry.async_create(
        scope="automation",
        name="Something else",
        icon="mdi:leaf",
    )

    expect(
        lambda: category_registry.async_update(
            scope="automation",
            category_id=category2.category_id,
            name="ENERGY SAVING",
        )
    ).to_raise(ValueError, match=r"The name 'ENERGY SAVING' is already in use")

    expect(category1.name).to_equal("Energy saving")
    expect(category2.name).to_equal("Something else")
    expect(len(category_registry.categories["automation"])).to_equal(2)


@test
async def load_categories(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Make sure that we can load/save data correctly."""
    category1 = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    category2 = category_registry.async_create(
        scope="automation",
        name="Something else",
        icon="mdi:leaf",
    )
    category3 = category_registry.async_create(
        scope="zone",
        name="Grocery stores",
        icon="mdi:store",
    )

    expect(len(category_registry.categories)).to_equal(2)
    expect(len(category_registry.categories["automation"])).to_equal(2)
    expect(len(category_registry.categories["zone"])).to_equal(1)

    registry2 = cr.CategoryRegistry(hass)
    await flush_store(category_registry._store)
    await registry2.async_load()

    expect(len(registry2.categories)).to_equal(2)
    expect(len(registry2.categories["automation"])).to_equal(2)
    expect(len(registry2.categories["zone"])).to_equal(1)
    expect(list(category_registry.categories)).to_equal(list(registry2.categories))
    expect(list(category_registry.categories["automation"])).to_equal(
        list(registry2.categories["automation"])
    )
    expect(list(category_registry.categories["zone"])).to_equal(
        list(registry2.categories["zone"])
    )

    category1_registry2 = registry2.async_get_category(
        scope="automation", category_id=category1.category_id
    )
    expect(category1_registry2.category_id).to_equal(category1.category_id)
    expect(category1_registry2.name).to_equal(category1.name)
    expect(category1_registry2.icon).to_equal(category1.icon)

    category2_registry2 = registry2.async_get_category(
        scope="automation", category_id=category2.category_id
    )
    expect(category2_registry2.category_id).to_equal(category2.category_id)
    expect(category2_registry2.name).to_equal(category2.name)
    expect(category2_registry2.icon).to_equal(category2.icon)

    category3_registry2 = registry2.async_get_category(
        scope="zone", category_id=category3.category_id
    )
    expect(category3_registry2.category_id).to_equal(category3.category_id)
    expect(category3_registry2.name).to_equal(category3.name)
    expect(category3_registry2.icon).to_equal(category3.icon)


@test
async def loading_categories_from_storage(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading stored categories on start."""
    date_1 = datetime(2024, 2, 14, 12, 0, 0)
    date_2 = datetime(2024, 2, 14, 12, 0, 0)
    hass_storage[cr.STORAGE_KEY] = {
        "version": cr.STORAGE_VERSION_MAJOR,
        "minor_version": cr.STORAGE_VERSION_MINOR,
        "data": {
            "categories": {
                "automation": [
                    {
                        "category_id": "uuid1",
                        "created_at": date_1.isoformat(),
                        "modified_at": date_1.isoformat(),
                        "name": "Energy saving",
                        "icon": "mdi:leaf",
                    },
                    {
                        "category_id": "uuid2",
                        "created_at": date_1.isoformat(),
                        "modified_at": date_2.isoformat(),
                        "name": "Something else",
                        "icon": None,
                    },
                ],
                "zone": [
                    {
                        "category_id": "uuid3",
                        "created_at": date_2.isoformat(),
                        "modified_at": date_2.isoformat(),
                        "name": "Grocery stores",
                        "icon": "mdi:store",
                    },
                ],
            }
        },
    }

    await cr.async_load(hass)
    category_registry = cr.async_get(hass)

    expect(len(category_registry.categories)).to_equal(2)
    expect(len(category_registry.categories["automation"])).to_equal(2)
    expect(len(category_registry.categories["zone"])).to_equal(1)

    category1 = category_registry.async_get_category(
        scope="automation", category_id="uuid1"
    )
    expect(category1).to_equal(
        cr.CategoryEntry(
            category_id="uuid1",
            created_at=date_1,
            modified_at=date_1,
            name="Energy saving",
            icon="mdi:leaf",
        )
    )

    category2 = category_registry.async_get_category(
        scope="automation", category_id="uuid2"
    )
    expect(category2).to_equal(
        cr.CategoryEntry(
            category_id="uuid2",
            created_at=date_1,
            modified_at=date_2,
            name="Something else",
            icon=None,
        )
    )

    category3 = category_registry.async_get_category(scope="zone", category_id="uuid3")
    expect(category3).to_equal(
        cr.CategoryEntry(
            category_id="uuid3",
            created_at=date_2,
            modified_at=date_2,
            name="Grocery stores",
            icon="mdi:store",
        )
    )


@test
async def async_create_thread_safety(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Test async_create raises when called from wrong thread."""
    err: RuntimeError | None = None
    try:
        await hass.async_add_executor_job(
            partial(category_registry.async_create, name="any", scope="any")
        )
    except RuntimeError as e:
        err = e
    expect(err).not_.to_be_none()
    expect(
        "Detected code that calls category_registry.async_create from a thread"
        in str(err)
    ).to_be(True)


@test
async def async_delete_thread_safety(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Test async_delete raises when called from wrong thread."""
    any_category = category_registry.async_create(name="any", scope="any")

    err: RuntimeError | None = None
    try:
        await hass.async_add_executor_job(
            partial(
                category_registry.async_delete,
                scope="any",
                category_id=any_category.category_id,
            )
        )
    except RuntimeError as e:
        err = e
    expect(err).not_.to_be_none()
    expect(
        "Detected code that calls category_registry.async_delete from a thread"
        in str(err)
    ).to_be(True)


@test
async def async_update_thread_safety(
    hass: HomeAssistant = Depends(hass),
    category_registry: cr.CategoryRegistry = Depends(category_registry),
) -> None:
    """Test async_update raises when called from wrong thread."""
    any_category = category_registry.async_create(name="any", scope="any")

    err: RuntimeError | None = None
    try:
        await hass.async_add_executor_job(
            partial(
                category_registry.async_update,
                scope="any",
                category_id=any_category.category_id,
                name="new name",
            )
        )
    except RuntimeError as e:
        err = e
    expect(err).not_.to_be_none()
    expect(
        "Detected code that calls category_registry.async_update from a thread"
        in str(err)
    ).to_be(True)


@test
async def migration_from_1_1(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migration from version 1.1."""
    hass_storage[cr.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "categories": {
                "automation": [
                    {
                        "category_id": "uuid1",
                        "name": "Energy saving",
                        "icon": "mdi:leaf",
                    },
                    {
                        "category_id": "uuid2",
                        "name": "Something else",
                        "icon": None,
                    },
                ],
                "zone": [
                    {
                        "category_id": "uuid3",
                        "name": "Grocery stores",
                        "icon": "mdi:store",
                    },
                ],
            }
        },
    }

    await cr.async_load(hass)
    registry = cr.async_get(hass)

    expect(len(registry.categories)).to_equal(2)
    expect(len(registry.categories["automation"])).to_equal(2)
    expect(len(registry.categories["zone"])).to_equal(1)

    expect(
        bool(registry.async_get_category(scope="automation", category_id="uuid1"))
    ).to_be(True)

    await flush_store(registry._store)
    expect(hass_storage[cr.STORAGE_KEY]).to_equal(
        {
            "version": cr.STORAGE_VERSION_MAJOR,
            "minor_version": cr.STORAGE_VERSION_MINOR,
            "key": cr.STORAGE_KEY,
            "data": {
                "categories": {
                    "automation": [
                        {
                            "category_id": "uuid1",
                            "created_at": "1970-01-01T00:00:00+00:00",
                            "modified_at": "1970-01-01T00:00:00+00:00",
                            "name": "Energy saving",
                            "icon": "mdi:leaf",
                        },
                        {
                            "category_id": "uuid2",
                            "created_at": "1970-01-01T00:00:00+00:00",
                            "modified_at": "1970-01-01T00:00:00+00:00",
                            "name": "Something else",
                            "icon": None,
                        },
                    ],
                    "zone": [
                        {
                            "category_id": "uuid3",
                            "created_at": "1970-01-01T00:00:00+00:00",
                            "modified_at": "1970-01-01T00:00:00+00:00",
                            "name": "Grocery stores",
                            "icon": "mdi:store",
                        },
                    ],
                }
            },
        }
    )
