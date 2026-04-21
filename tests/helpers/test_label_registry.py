"""Tests for the Label Registry."""

from datetime import datetime
from functools import partial
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    label_registry as lr,
)
from homeassistant.util.dt import utcnow

from tests.common import MockConfigEntry, async_capture_events, flush_store
from tests.hass_fixtures import (
    device_registry,
    entity_registry,
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


@test
async def list_labels(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can read label."""
    labels = label_registry.async_list_labels()
    expect(len(list(labels))).to_equal(len(label_registry.labels))


@test
async def create_label(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can create labels."""
    del freezer  # activates freezegun for utcnow()
    update_events = async_capture_events(hass, lr.EVENT_LABEL_REGISTRY_UPDATED)
    label = label_registry.async_create(
        name="My Label",
        color="#FF0000",
        icon="mdi:test",
        description="This label is for testing",
    )

    expect(label).to_equal(
        lr.LabelEntry(
            label_id="my_label",
            name="My Label",
            color="#FF0000",
            icon="mdi:test",
            description="This label is for testing",
            created_at=utcnow(),
            modified_at=utcnow(),
        )
    )

    expect(len(label_registry.labels)).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[0].data).to_equal(
        {"action": "create", "label_id": label.label_id}
    )


@test
async def create_label_with_name_already_in_use(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can't create a label with a ID already in use."""
    update_events = async_capture_events(hass, lr.EVENT_LABEL_REGISTRY_UPDATED)
    label_registry.async_create("mock")

    expect(lambda: label_registry.async_create("mock")).to_raise(
        ValueError, match=r"The name mock \(mock\) is already in use"
    )

    await hass.async_block_till_done()

    expect(len(label_registry.labels)).to_equal(1)
    expect(len(update_events)).to_equal(1)


@test
async def create_label_with_id_already_in_use(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can't create a label with a name already in use."""
    label = label_registry.async_create("Label")

    updated_label = label_registry.async_update(label.label_id, name="Renamed Label")
    expect(updated_label.label_id).to_equal(label.label_id)

    second_label = label_registry.async_create("Label")
    expect(label.label_id != second_label.label_id).to_be(True)
    expect(second_label.label_id).to_equal("label_2")


@test
async def delete_label(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can delete a label."""
    update_events = async_capture_events(hass, lr.EVENT_LABEL_REGISTRY_UPDATED)
    label = label_registry.async_create("Label")
    expect(len(label_registry.labels)).to_equal(1)

    label_registry.async_delete(label.label_id)

    expect(bool(label_registry.labels)).to_be(False)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {"action": "create", "label_id": label.label_id}
    )
    expect(update_events[1].data).to_equal(
        {"action": "remove", "label_id": label.label_id}
    )


@test
async def delete_non_existing_label(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can't delete a label that doesn't exist."""
    label_registry.async_create("mock")

    expect(lambda: label_registry.async_delete("")).to_raise(KeyError)

    expect(len(label_registry.labels)).to_equal(1)


@test
async def update_label(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can update labels."""
    created_at = datetime.fromisoformat("2024-01-01T01:00:00+00:00")
    freezer.move_to(created_at)
    update_events = async_capture_events(hass, lr.EVENT_LABEL_REGISTRY_UPDATED)
    label = label_registry.async_create("Mock")

    expect(len(label_registry.labels)).to_equal(1)
    expect(label).to_equal(
        lr.LabelEntry(
            label_id="mock",
            name="Mock",
            color=None,
            icon=None,
            description=None,
            created_at=created_at,
            modified_at=created_at,
        )
    )

    modified_at = datetime.fromisoformat("2024-02-01T01:00:00+00:00")
    freezer.move_to(modified_at)
    updated_label = label_registry.async_update(
        label.label_id,
        name="Updated",
        color="#FFFFFF",
        icon="mdi:update",
        description="Updated description",
    )

    expect(updated_label != label).to_be(True)
    expect(updated_label).to_equal(
        lr.LabelEntry(
            label_id="mock",
            name="Updated",
            color="#FFFFFF",
            icon="mdi:update",
            description="Updated description",
            created_at=created_at,
            modified_at=modified_at,
        )
    )
    expect(len(label_registry.labels)).to_equal(1)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(2)
    expect(update_events[0].data).to_equal(
        {"action": "create", "label_id": label.label_id}
    )
    expect(update_events[1].data).to_equal(
        {"action": "update", "label_id": label.label_id}
    )


@test
async def update_label_with_same_data(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can reapply the same data to the label and it won't update."""
    update_events = async_capture_events(hass, lr.EVENT_LABEL_REGISTRY_UPDATED)
    label = label_registry.async_create(
        "mock",
        color="#FFFFFF",
        icon="mdi:test",
        description="Description",
    )

    udpated_label = label_registry.async_update(
        label_id=label.label_id,
        name="mock",
        color="#FFFFFF",
        icon="mdi:test",
        description="Description",
    )
    expect(label).to_equal(udpated_label)

    await hass.async_block_till_done()

    expect(len(update_events)).to_equal(1)
    expect(update_events[0].data).to_equal(
        {"action": "create", "label_id": label.label_id}
    )


@test
async def update_label_with_same_name_change_case(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can reapply the same name with a different case to the label."""
    label = label_registry.async_create("mock")

    updated_label = label_registry.async_update(label.label_id, name="Mock")

    expect(updated_label.name).to_equal("Mock")
    expect(updated_label.label_id).to_equal(label.label_id)
    expect(updated_label.normalized_name).to_equal(label.normalized_name)
    expect(len(label_registry.labels)).to_equal(1)


@test
async def update_label_with_name_already_in_use(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can't update a label with a name already in use."""
    label1 = label_registry.async_create("mock1")
    label2 = label_registry.async_create("mock2")

    expect(
        lambda: label_registry.async_update(label1.label_id, name="mock2")
    ).to_raise(ValueError, match=r"The name mock2 \(mock2\) is already in use")

    expect(label1.name).to_equal("mock1")
    expect(label2.name).to_equal("mock2")
    expect(len(label_registry.labels)).to_equal(2)


@test
async def update_label_with_normalized_name_already_in_use(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure that we can't update a label with a normalized name already in use."""
    label1 = label_registry.async_create("mock1")
    label2 = label_registry.async_create("M O C K 2")

    expect(
        lambda: label_registry.async_update(label1.label_id, name="mock2")
    ).to_raise(ValueError, match=r"The name mock2 \(mock2\) is already in use")

    expect(label1.name).to_equal("mock1")
    expect(label2.name).to_equal("M O C K 2")
    expect(len(label_registry.labels)).to_equal(2)


@test
async def load_labels(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
    freezer: FrozenDateTimeFactory = Depends(freezer),
) -> None:
    """Make sure that we can load/save data correctly."""
    label1_created = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
    freezer.move_to(label1_created)
    label1 = label_registry.async_create(
        "Label One",
        color="#FF000",
        icon="mdi:one",
        description="This label is label one",
    )
    label2_created = datetime.fromisoformat("2024-02-01T00:00:00+00:00")
    freezer.move_to(label2_created)
    label2 = label_registry.async_create(
        "Label Two",
        color="#000FF",
        icon="mdi:two",
        description="This label is label two",
    )

    expect(len(label_registry.labels)).to_equal(2)

    registry2 = lr.LabelRegistry(hass)
    await flush_store(label_registry._store)
    await registry2.async_load()

    expect(len(registry2.labels)).to_equal(2)
    expect(list(label_registry.labels)).to_equal(list(registry2.labels))

    label1_registry2 = registry2.async_get_label_by_name("Label One")
    expect(label1_registry2).to_equal(label1)

    label2_registry2 = registry2.async_get_label_by_name("Label Two")
    expect(label2_registry2).to_equal(label2)


@test
async def loading_label_from_storage(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test loading stored labels on start."""
    hass_storage[lr.STORAGE_KEY] = {
        "version": lr.STORAGE_VERSION_MAJOR,
        "data": {
            "labels": [
                {
                    "color": "#FFFFFF",
                    "description": None,
                    "icon": "mdi:test",
                    "label_id": "one",
                    "name": "One",
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "modified_at": "2024-02-01T00:00:00+00:00",
                }
            ]
        },
    }

    await lr.async_load(hass)
    registry = lr.async_get(hass)

    expect(len(registry.labels)).to_equal(1)


@test
async def getting_label(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure we can get the labels by name."""
    label = label_registry.async_create("Mock1")
    label2 = label_registry.async_get_label_by_name("mock1")
    label3 = label_registry.async_get_label_by_name("mock   1")

    expect(label).to_equal(label2)
    expect(label).to_equal(label3)
    expect(label2).to_equal(label3)

    get_label = label_registry.async_get_label(label.label_id)
    expect(get_label).to_equal(label)


@test
async def async_get_label_by_name_not_found(
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Make sure we return None for non-existent labels."""
    label_registry.async_create("Mock1")

    expect(len(label_registry.labels)).to_equal(1)

    expect(label_registry.async_get_label_by_name("non_exist")).to_be_none()


@test
async def labels_removed_from_devices(
    hass: HomeAssistant = Depends(hass),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Test if label gets removed from devices when the label is removed."""
    config_entry = MockConfigEntry()
    config_entry.add_to_hass(hass)

    label1 = label_registry.async_create("label1")
    label2 = label_registry.async_create("label2")
    expect(len(label_registry.labels)).to_equal(2)

    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:23")},
        identifiers={("bridgeid", "0123")},
        manufacturer="manufacturer",
        model="model",
    )
    device_registry.async_update_device(entry.id, labels={label1.label_id})
    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:56")},
        identifiers={("bridgeid", "0456")},
        manufacturer="manufacturer",
        model="model",
    )
    device_registry.async_update_device(entry.id, labels={label2.label_id})
    entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:89")},
        identifiers={("bridgeid", "0789")},
        manufacturer="manufacturer",
        model="model",
    )
    device_registry.async_update_device(
        entry.id, labels={label1.label_id, label2.label_id}
    )

    entries = dr.async_entries_for_label(device_registry, label1.label_id)
    expect(len(entries)).to_equal(2)
    entries = dr.async_entries_for_label(device_registry, label2.label_id)
    expect(len(entries)).to_equal(2)

    label_registry.async_delete(label1.label_id)
    await hass.async_block_till_done()

    entries = dr.async_entries_for_label(device_registry, label1.label_id)
    expect(len(entries)).to_equal(0)
    entries = dr.async_entries_for_label(device_registry, label2.label_id)
    expect(len(entries)).to_equal(2)

    label_registry.async_delete(label2.label_id)
    await hass.async_block_till_done()

    entries = dr.async_entries_for_label(device_registry, label1.label_id)
    expect(len(entries)).to_equal(0)
    entries = dr.async_entries_for_label(device_registry, label2.label_id)
    expect(len(entries)).to_equal(0)


@test
async def labels_removed_from_entities(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Test if label gets removed from entity when the label is removed."""
    label1 = label_registry.async_create("label1")
    label2 = label_registry.async_create("label2")
    expect(len(label_registry.labels)).to_equal(2)

    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="123",
    )
    entity_registry.async_update_entity(entry.entity_id, labels={label1.label_id})
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="456",
    )
    entity_registry.async_update_entity(entry.entity_id, labels={label2.label_id})
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="789",
    )
    entity_registry.async_update_entity(
        entry.entity_id, labels={label1.label_id, label2.label_id}
    )

    entries = er.async_entries_for_label(entity_registry, label1.label_id)
    expect(len(entries)).to_equal(2)
    entries = er.async_entries_for_label(entity_registry, label2.label_id)
    expect(len(entries)).to_equal(2)

    label_registry.async_delete(label1.label_id)
    await hass.async_block_till_done()

    entries = er.async_entries_for_label(entity_registry, label1.label_id)
    expect(len(entries)).to_equal(0)
    entries = er.async_entries_for_label(entity_registry, label2.label_id)
    expect(len(entries)).to_equal(2)

    label_registry.async_delete(label2.label_id)
    await hass.async_block_till_done()

    entries = er.async_entries_for_label(entity_registry, label1.label_id)
    expect(len(entries)).to_equal(0)
    entries = er.async_entries_for_label(entity_registry, label2.label_id)
    expect(len(entries)).to_equal(0)


@test
async def async_create_thread_safety(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Test async_create raises when called from wrong thread."""
    err: RuntimeError | None = None
    try:
        await hass.async_add_executor_job(label_registry.async_create, "any")
    except RuntimeError as e:
        err = e
    expect(err).not_.to_be_none()
    expect(
        "Detected code that calls label_registry.async_create from a thread"
        in str(err)
    ).to_be(True)


@test
async def async_delete_thread_safety(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Test async_delete raises when called from wrong thread."""
    any_label = label_registry.async_create("any")

    err: RuntimeError | None = None
    try:
        await hass.async_add_executor_job(label_registry.async_delete, any_label)
    except RuntimeError as e:
        err = e
    expect(err).not_.to_be_none()
    expect(
        "Detected code that calls label_registry.async_delete from a thread"
        in str(err)
    ).to_be(True)


@test
async def async_update_thread_safety(
    hass: HomeAssistant = Depends(hass),
    label_registry: lr.LabelRegistry = Depends(label_registry),
) -> None:
    """Test async_update raises when called from wrong thread."""
    any_label = label_registry.async_create("any")

    err: RuntimeError | None = None
    try:
        await hass.async_add_executor_job(
            partial(label_registry.async_update, any_label.label_id, name="new name")
        )
    except RuntimeError as e:
        err = e
    expect(err).not_.to_be_none()
    expect(
        "Detected code that calls label_registry.async_update from a thread"
        in str(err)
    ).to_be(True)


@test
async def migration_from_1_1(
    hass: HomeAssistant = Depends(hass_unloaded),
    hass_storage: dict[str, Any] = Depends(hass_storage),
) -> None:
    """Test migration from version 1.1."""
    hass_storage[lr.STORAGE_KEY] = {
        "version": 1,
        "data": {
            "labels": [
                {
                    "color": None,
                    "description": None,
                    "icon": None,
                    "label_id": "12345A",
                    "name": "mock",
                }
            ]
        },
    }

    await lr.async_load(hass)
    registry = lr.async_get(hass)

    entry = registry.async_get_label_by_name("mock")
    expect(entry.label_id).to_equal("12345A")

    await flush_store(registry._store)
    expect(hass_storage[lr.STORAGE_KEY]).to_equal(
        {
            "version": lr.STORAGE_VERSION_MAJOR,
            "minor_version": lr.STORAGE_VERSION_MINOR,
            "key": lr.STORAGE_KEY,
            "data": {
                "labels": [
                    {
                        "color": None,
                        "description": None,
                        "icon": None,
                        "label_id": "12345A",
                        "name": "mock",
                        "created_at": "1970-01-01T00:00:00+00:00",
                        "modified_at": "1970-01-01T00:00:00+00:00",
                    }
                ]
            },
        }
    )
