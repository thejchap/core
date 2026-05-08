"""Tests for the HomeKit IID manager (tryke port)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tryke import Depends, expect, fixture, test

from homeassistant.components.homekit.const import DOMAIN
from homeassistant.components.homekit.iidmanager import (
    AccessoryIIDStorage,
    get_iid_storage_filename_for_entry_id,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.json import json_loads
from homeassistant.util.uuid import random_uuid_hex

from tests.common import MockConfigEntry, async_load_fixture
from tests.components.homekit._fixtures import iid_storage as iid_storage_fixture
from tests.hass_fixtures import (
    hass as hass_fixture,
    hass_storage as hass_storage_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (see PATTERNS.md)."""
    return hass


@test
async def iid_generation_and_restore(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test generating iids and restoring them from storage."""
    del iid_storage  # consumer rebuilds storage from entry below
    del hass_storage
    entry = MockConfigEntry(domain=DOMAIN)

    iid_storage = AccessoryIIDStorage(hass, entry.entry_id)
    await iid_storage.async_initialize()

    random_service_uuid = UUID(random_uuid_hex())
    random_characteristic_uuid = UUID(random_uuid_hex())

    iid1 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, None, random_characteristic_uuid, None
    )
    iid2 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, None, random_characteristic_uuid, None
    )
    expect(iid1).to_be(iid2)

    service_only_iid1 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, None, None, None
    )
    service_only_iid2 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, None, None, None
    )
    expect(service_only_iid1).to_be(service_only_iid2)
    expect(service_only_iid1 != iid1).to_be(True)

    service_only_iid_with_unique_id1 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, "any", None, None
    )
    service_only_iid_with_unique_id2 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, "any", None, None
    )
    expect(service_only_iid_with_unique_id1).to_be(service_only_iid_with_unique_id2)
    expect(service_only_iid_with_unique_id1 != service_only_iid1).to_be(True)

    unique_char_iid1 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, None, random_characteristic_uuid, "any"
    )
    unique_char_iid2 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, None, random_characteristic_uuid, "any"
    )
    expect(unique_char_iid1).to_be(unique_char_iid2)
    expect(unique_char_iid1 != iid1).to_be(True)

    unique_service_unique_char_iid1 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, "any", random_characteristic_uuid, "any"
    )
    unique_service_unique_char_iid2 = iid_storage.get_or_allocate_iid(
        1, random_service_uuid, "any", random_characteristic_uuid, "any"
    )
    expect(unique_service_unique_char_iid1).to_be(unique_service_unique_char_iid2)
    expect(unique_service_unique_char_iid1 != iid1).to_be(True)

    unique_service_unique_char_new_aid_iid1 = iid_storage.get_or_allocate_iid(
        2, random_service_uuid, "any", random_characteristic_uuid, "any"
    )
    unique_service_unique_char_new_aid_iid2 = iid_storage.get_or_allocate_iid(
        2, random_service_uuid, "any", random_characteristic_uuid, "any"
    )
    expect(unique_service_unique_char_new_aid_iid1).to_be(
        unique_service_unique_char_new_aid_iid2
    )
    await iid_storage.async_save()

    iid_storage2 = AccessoryIIDStorage(hass, entry.entry_id)
    await iid_storage2.async_initialize()
    iid3 = iid_storage2.get_or_allocate_iid(
        1, random_service_uuid, None, random_characteristic_uuid, None
    )
    expect(iid3).to_be(iid1)


@test
async def iid_storage_filename(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test iid storage uses the expected filename."""
    del iid_storage
    del hass_storage
    entry = MockConfigEntry(domain=DOMAIN)

    iid_storage = AccessoryIIDStorage(hass, entry.entry_id)
    await iid_storage.async_initialize()
    expect(
        iid_storage.store.path.endswith(
            get_iid_storage_filename_for_entry_id(entry.entry_id)
        )
    ).to_be(True)


@test
async def iid_migration_to_v2(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test iid storage migration."""
    del iid_storage
    v1_iids = json_loads(await async_load_fixture(hass, "iids_v1", DOMAIN))
    v2_iids = json_loads(await async_load_fixture(hass, "iids_v2", DOMAIN))
    hass_storage["homekit.v1.iids"] = v1_iids
    hass_storage["homekit.v2.iids"] = v2_iids

    iid_storage_v2 = AccessoryIIDStorage(hass, "v1")
    await iid_storage_v2.async_initialize()

    iid_storage_v1 = AccessoryIIDStorage(hass, "v2")
    await iid_storage_v1.async_initialize()

    expect(iid_storage_v1.allocations == iid_storage_v2.allocations).to_be(True)
    expect(iid_storage_v1.allocated_iids == iid_storage_v2.allocated_iids).to_be(True)

    expect(len(iid_storage_v2.allocations)).to_be(12)

    for allocations in iid_storage_v2.allocations.values():
        expect(allocations["3E___"]).to_be(1)


@test
async def iid_migration_to_v2_with_underscore(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test iid storage migration with underscore."""
    del iid_storage
    v1_iids = json_loads(
        await async_load_fixture(hass, "iids_v1_with_underscore", DOMAIN)
    )
    v2_iids = json_loads(
        await async_load_fixture(hass, "iids_v2_with_underscore", DOMAIN)
    )
    hass_storage["homekit.v1_with_underscore.iids"] = v1_iids
    hass_storage["homekit.v2_with_underscore.iids"] = v2_iids

    iid_storage_v2 = AccessoryIIDStorage(hass, "v1_with_underscore")
    await iid_storage_v2.async_initialize()

    iid_storage_v1 = AccessoryIIDStorage(hass, "v2_with_underscore")
    await iid_storage_v1.async_initialize()

    expect(iid_storage_v1.allocations == iid_storage_v2.allocations).to_be(True)
    expect(iid_storage_v1.allocated_iids == iid_storage_v2.allocated_iids).to_be(True)

    expect(len(iid_storage_v2.allocations)).to_be(2)

    for allocations in iid_storage_v2.allocations.values():
        expect(allocations["3E___"]).to_be(1)


@test
async def iid_generation_and_restore_v2(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    iid_storage: AccessoryIIDStorage = Depends(iid_storage_fixture),
    hass_storage: dict[str, Any] = Depends(hass_storage_fixture),
) -> None:
    """Test generating iids and restoring them from storage (v2 layout)."""
    del iid_storage
    del hass_storage
    entry = MockConfigEntry(domain=DOMAIN)

    iid_storage = AccessoryIIDStorage(hass, entry.entry_id)
    await iid_storage.async_initialize()
    not_accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        1, "000000AA-0000-1000-8000-0026BB765291", None, None, None
    )
    expect(not_accessory_info_service_iid).to_be(2)
    expect(iid_storage.allocated_iids == {"1": [1, 2]}).to_be(True)
    not_accessory_info_service_iid_2 = iid_storage.get_or_allocate_iid(
        1, "000000BB-0000-1000-8000-0026BB765291", None, None, None
    )
    expect(not_accessory_info_service_iid_2).to_be(3)
    expect(iid_storage.allocated_iids == {"1": [1, 2, 3]}).to_be(True)
    not_accessory_info_service_iid_2 = iid_storage.get_or_allocate_iid(
        1, "000000BB-0000-1000-8000-0026BB765291", None, None, None
    )
    expect(not_accessory_info_service_iid_2).to_be(3)
    expect(iid_storage.allocated_iids == {"1": [1, 2, 3]}).to_be(True)
    accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        1, "0000003E-0000-1000-8000-0026BB765291", None, None, None
    )
    expect(accessory_info_service_iid).to_be(1)
    expect(iid_storage.allocated_iids == {"1": [1, 2, 3]}).to_be(True)
    accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        1, "0000003E-0000-1000-8000-0026BB765291", None, None, None
    )
    expect(accessory_info_service_iid).to_be(1)
    expect(iid_storage.allocated_iids == {"1": [1, 2, 3]}).to_be(True)
    accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        2, "0000003E-0000-1000-8000-0026BB765291", None, None, None
    )
    expect(accessory_info_service_iid).to_be(1)
    expect(iid_storage.allocated_iids == {"1": [1, 2, 3], "2": [1]}).to_be(True)
