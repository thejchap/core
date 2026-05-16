"""Tests for BSB-LAN services."""

from datetime import time
from typing import Any
from unittest.mock import MagicMock

from bsblan import BSBLANError, DaySchedule, DeviceTime, TimeSlot
from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.bsblan.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from ._fixtures import (
    mock_bsblan as mock_bsblan_fixture,
    mock_config_entry as mock_config_entry_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async

# Test constants
TEST_DEVICE_MAC = "00:80:41:19:69:90"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


async def _setup_and_get_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> dr.DeviceEntry:
    """Set up the integration and return the device entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_DEVICE_MAC)})
    expect(device).not_.to_be_none()
    return device


@test.cases(
    test.case(
        "multiple_slots_per_day",
        service_data={
            "monday_slots": [
                {"start_time": time(6, 0), "end_time": time(8, 0)},
                {"start_time": time(17, 0), "end_time": time(21, 0)},
            ],
            "tuesday_slots": [
                {"start_time": time(6, 0), "end_time": time(8, 0)},
            ],
        },
        expected_schedules={
            "monday": DaySchedule(
                slots=[
                    TimeSlot(start=time(6, 0), end=time(8, 0)),
                    TimeSlot(start=time(17, 0), end=time(21, 0)),
                ]
            ),
            "tuesday": DaySchedule(
                slots=[TimeSlot(start=time(6, 0), end=time(8, 0))]
            ),
        },
    ),
    test.case(
        "weekend_schedule",
        service_data={
            "friday_slots": [
                {"start_time": time(17, 0), "end_time": time(21, 0)},
            ],
            "saturday_slots": [
                {"start_time": time(8, 0), "end_time": time(22, 0)},
            ],
        },
        expected_schedules={
            "friday": DaySchedule(
                slots=[TimeSlot(start=time(17, 0), end=time(21, 0))]
            ),
            "saturday": DaySchedule(
                slots=[TimeSlot(start=time(8, 0), end=time(22, 0))]
            ),
        },
    ),
    test.case(
        "single_day",
        service_data={
            "wednesday_slots": [
                {"start_time": time(6, 0), "end_time": time(8, 0)},
            ],
        },
        expected_schedules={
            "wednesday": DaySchedule(
                slots=[TimeSlot(start=time(6, 0), end=time(8, 0))]
            ),
        },
    ),
    test.case(
        "clear_schedule_with_empty_array",
        service_data={"monday_slots": []},
        expected_schedules={"monday": DaySchedule(slots=[])},
    ),
)
async def set_hot_water_schedule(
    service_data: dict[str, Any],
    expected_schedules: dict[str, DaySchedule],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test setting hot water schedule with various configurations."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)

    service_call_data = {"device_id": device_entry.id}
    service_call_data.update(service_data)

    await hass.services.async_call(
        DOMAIN,
        "set_hot_water_schedule",
        service_call_data,
        blocking=True,
    )

    expect(len(mock_bsblan.set_hot_water_schedule.mock_calls)).to_equal(1)
    call_args = mock_bsblan.set_hot_water_schedule.call_args

    dhw_schedule = call_args.args[0]
    for key, expected_schedule in expected_schedules.items():
        actual_schedule = getattr(dhw_schedule, key)
        expect(actual_schedule).to_equal(expected_schedule)


@test
async def invalid_device_id(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
) -> None:
    """Test error when device ID is invalid."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            "set_hot_water_schedule",
            {
                "device_id": "invalid_device_id",
                "monday_slots": [
                    {"start_time": time(6, 0), "end_time": time(8, 0)},
                ],
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("invalid_device_id")


@test.cases(
    test.case(
        "set_hot_water_schedule",
        service_name="set_hot_water_schedule",
        service_data={
            "monday_slots": [{"start_time": time(6, 0), "end_time": time(8, 0)}]
        },
    ),
    test.case("sync_time", service_name="sync_time", service_data={}),
)
async def no_config_entry_for_device(
    service_name: str,
    service_data: dict[str, Any],
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test error when device has no matching BSB-LAN config entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    other_entry = MockConfigEntry(domain="other_domain", data={})
    other_entry.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=other_entry.entry_id,
        identifiers={("other_domain", "other_device")},
        name="Other Device",
    )

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            service_name,
            {"device_id": device_entry.id, **service_data},
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("no_config_entry_for_device")


@test
async def config_entry_not_loaded(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test error when config entry is not loaded."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)
    await hass.config_entries.async_unload(mock_config_entry.entry_id)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            "set_hot_water_schedule",
            {
                "device_id": device_entry.id,
                "monday_slots": [
                    {"start_time": time(6, 0), "end_time": time(8, 0)},
                ],
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("config_entry_not_loaded")


@test
async def api_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test error when BSB-LAN API call fails."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)
    mock_bsblan.set_hot_water_schedule.side_effect = BSBLANError("API Error")

    raised: HomeAssistantError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            "set_hot_water_schedule",
            {
                "device_id": device_entry.id,
                "monday_slots": [
                    {"start_time": time(6, 0), "end_time": time(8, 0)},
                ],
            },
            blocking=True,
        )
    except HomeAssistantError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal("set_schedule_failed")


@test.cases(
    test.case(
        "time_objects_end_before_start",
        start_time=time(13, 0),
        end_time=time(11, 0),
        expected_error="end_time_before_start_time",
    ),
    test.case(
        "strings_end_before_start",
        start_time="13:00",
        end_time="11:00",
        expected_error="end_time_before_start_time",
    ),
)
async def time_validation_errors(
    start_time: time | str,
    end_time: time | str,
    expected_error: str,
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test validation errors for various time input scenarios."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)

    raised: ServiceValidationError | None = None
    try:
        await hass.services.async_call(
            DOMAIN,
            "set_hot_water_schedule",
            {
                "device_id": device_entry.id,
                "monday_slots": [
                    {"start_time": start_time, "end_time": end_time},
                ],
            },
            blocking=True,
        )
    except ServiceValidationError as exc:
        raised = exc

    expect(raised).not_.to_be_none()
    expect(raised.translation_key).to_equal(expected_error)


@test
async def unprovided_days_are_none(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test that unprovided days are sent as None to BSB-LAN API."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)

    await hass.services.async_call(
        DOMAIN,
        "set_hot_water_schedule",
        {
            "device_id": device_entry.id,
            "monday_slots": [
                {"start_time": time(6, 0), "end_time": time(8, 0)},
            ],
            "tuesday_slots": [
                {"start_time": time(17, 0), "end_time": time(21, 0)},
            ],
        },
        blocking=True,
    )

    expect(mock_bsblan.set_hot_water_schedule.called).to_be_truthy()
    call_args = mock_bsblan.set_hot_water_schedule.call_args
    dhw_schedule = call_args.args[0]

    expect(dhw_schedule.monday).to_equal(
        DaySchedule(slots=[TimeSlot(start=time(6, 0), end=time(8, 0))])
    )
    expect(dhw_schedule.tuesday).to_equal(
        DaySchedule(slots=[TimeSlot(start=time(17, 0), end=time(21, 0))])
    )

    expect(dhw_schedule.wednesday).to_be_none()
    expect(dhw_schedule.thursday).to_be_none()
    expect(dhw_schedule.friday).to_be_none()
    expect(dhw_schedule.saturday).to_be_none()
    expect(dhw_schedule.sunday).to_be_none()


@test
async def string_time_formats(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test service with string time formats."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)

    await hass.services.async_call(
        DOMAIN,
        "set_hot_water_schedule",
        {
            "device_id": device_entry.id,
            "monday_slots": [
                {"start_time": "06:00:00", "end_time": "08:00:00"},
            ],
            "tuesday_slots": [
                {"start_time": "17:00", "end_time": "21:00"},
            ],
        },
        blocking=True,
    )

    expect(mock_bsblan.set_hot_water_schedule.called).to_be_truthy()
    call_args = mock_bsblan.set_hot_water_schedule.call_args
    dhw_schedule = call_args.args[0]

    expect(dhw_schedule.monday).to_equal(
        DaySchedule(slots=[TimeSlot(start=time(6, 0), end=time(8, 0))])
    )
    expect(dhw_schedule.tuesday).to_equal(
        DaySchedule(slots=[TimeSlot(start=time(17, 0), end=time(21, 0))])
    )


@test
async def non_standard_time_types(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test service with non-standard time types raises error."""
    device_entry = await _setup_and_get_device(hass, mock_config_entry, device_registry)

    async with expect_raises_async(vol.MultipleInvalid):
        await hass.services.async_call(
            DOMAIN,
            "set_hot_water_schedule",
            {
                "device_id": device_entry.id,
                "monday_slots": [
                    {"start_time": 600, "end_time": 800},
                ],
            },
            blocking=True,
        )


@test
async def async_setup_services(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
) -> None:
    """Test service registration."""
    expect(hass.services.has_service(DOMAIN, "set_hot_water_schedule")).to_be_falsy()

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(hass.services.has_service(DOMAIN, "set_hot_water_schedule")).to_be_truthy()


@test
async def sync_time_service(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test the sync_time service."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_DEVICE_MAC)})
    expect(device).not_.to_be_none()

    mock_bsblan.time.return_value = DeviceTime.model_validate_json(
        '{"time": {"name": "Time", "value": "01.01.2020 00:00:00", "unit": "", "desc": "", "dataType": 0, "readonly": 0, "error": 0}}'
    )

    await hass.services.async_call(
        DOMAIN,
        "sync_time",
        {"device_id": device.id},
        blocking=True,
    )

    expect(mock_bsblan.time.called).to_be_truthy()

    current_time_str = dt_util.now().strftime("%d.%m.%Y %H:%M:%S")
    mock_bsblan.set_time.assert_called_once_with(current_time_str)


@test
async def sync_time_service_no_update_when_same(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test the sync_time service doesn't update when time matches."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_DEVICE_MAC)})
    expect(device).not_.to_be_none()

    current_time_str = dt_util.now().strftime("%d.%m.%Y %H:%M:%S")
    mock_bsblan.time.return_value = DeviceTime.model_validate_json(
        f'{{"time": {{"name": "Time", "value": "{current_time_str}", "unit": "", "desc": "", "dataType": 0, "readonly": 0, "error": 0}}}}'
    )

    await hass.services.async_call(
        DOMAIN,
        "sync_time",
        {"device_id": device.id},
        blocking=True,
    )

    expect(mock_bsblan.time.called).to_be_truthy()
    expect(mock_bsblan.set_time.called).to_be_falsy()


@test
async def sync_time_service_error_handling(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test the sync_time service handles errors gracefully."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_DEVICE_MAC)})
    expect(device).not_.to_be_none()

    mock_bsblan.time.side_effect = BSBLANError("Connection failed")

    async with expect_raises_async(HomeAssistantError, match="sync_time_failed"):
        await hass.services.async_call(
            DOMAIN,
            "sync_time",
            {"device_id": device.id},
            blocking=True,
        )


@test
async def sync_time_service_set_time_error(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test the sync_time service handles set_time errors."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(identifiers={(DOMAIN, TEST_DEVICE_MAC)})
    expect(device).not_.to_be_none()

    mock_bsblan.time.return_value = DeviceTime.model_validate_json(
        '{"time": {"name": "Time", "value": "01.01.2020 00:00:00", "unit": "", "desc": "", "dataType": 0, "readonly": 0, "error": 0}}'
    )

    mock_bsblan.set_time.side_effect = BSBLANError("Write failed")

    async with expect_raises_async(HomeAssistantError, match="sync_time_failed"):
        await hass.services.async_call(
            DOMAIN,
            "sync_time",
            {"device_id": device.id},
            blocking=True,
        )


@test
async def sync_time_service_entry_not_found(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
) -> None:
    """Test the sync_time service raises error for non-existent device."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "sync_time",
            {"device_id": "non_existent_device_id"},
            blocking=True,
        )


@test
async def sync_time_service_entry_not_loaded(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_bsblan: MagicMock = Depends(mock_bsblan_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test the sync_time service raises error for unloaded entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    unloaded_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Unloaded BSBLAN",
        data=mock_config_entry.data.copy(),
        unique_id="unloaded_unique_id",
    )
    unloaded_entry.add_to_hass(hass)

    unloaded_device = device_registry.async_get_or_create(
        config_entry_id=unloaded_entry.entry_id,
        identifiers={(DOMAIN, "unloaded_device_mac")},
        name="Unloaded Device",
    )

    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "sync_time",
            {"device_id": unloaded_device.id},
            blocking=True,
        )
