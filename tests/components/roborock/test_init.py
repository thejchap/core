"""Test for Roborock init."""

from __future__ import annotations

import pathlib
from typing import Any
from unittest.mock import AsyncMock, patch

from roborock import (
    RoborockInvalidCredentials,
    RoborockInvalidUserAgreement,
    RoborockNoUserAgreement,
)
from roborock.exceptions import RoborockException
from roborock.mqtt.session import MqttSessionUnauthorized
from tryke import Depends, expect, fixture, test

from homeassistant.components.roborock.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.helpers.device_registry import DeviceRegistry
from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.setup import async_setup_component

from ._fixtures import (
    FakeDevice,
    config_entry_data as config_entry_data_fixture,
    device_manager as device_manager_fixture,
    fake_devices as fake_devices_fixture,
    fake_vacuum as fake_vacuum_fixture,
    image_platforms_patch,
    mock_roborock_entry as mock_roborock_entry_fixture,
    no_platforms,
    sensor_platforms_patch,
    setup_entry as setup_entry_fixture,
    storage_path as storage_path_fixture,
)
from .mock_data import ROBOROCK_RRUID, USER_EMAIL

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor fixture for tryke Depends() resolution."""
    return 0


@test
async def unload_entry(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MockConfigEntry = Depends(setup_entry_fixture),
    device_manager: AsyncMock = Depends(device_manager_fixture),
) -> None:
    """Test unloading roborock integration."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(setup_entry.state).to_be(ConfigEntryState.LOADED)

    expect(device_manager.get_devices.called).to_be(True)
    expect(device_manager.close.called).to_be(False)

    expect(await hass.config_entries.async_unload(setup_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(setup_entry.state).to_be(ConfigEntryState.NOT_LOADED)

    expect(device_manager.close.called).to_be(True)


@test
async def home_assistant_stop(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: MockConfigEntry = Depends(setup_entry_fixture),
    device_manager: AsyncMock = Depends(device_manager_fixture),
) -> None:
    """Test shutting down Home Assistant."""
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(setup_entry.state).to_be(ConfigEntryState.LOADED)

    expect(device_manager.close.called).to_be(False)

    await hass.async_stop()

    expect(device_manager.close.called).to_be(True)


@test.cases(
    test.case("invalid_credentials", side_effect_cls=RoborockInvalidCredentials),
    test.case("mqtt_unauthorized", side_effect_cls=MqttSessionUnauthorized),
)
async def reauth_started(
    side_effect_cls: type[Exception],
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
) -> None:
    """Test reauth flow started."""
    with patch(
        "homeassistant.components.roborock.create_device_manager",
        side_effect=side_effect_cls(),
    ):
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        expect(mock_roborock_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")


@test
async def mqtt_session_unauthorized_hook_called(
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_manager: AsyncMock = Depends(device_manager_fixture),
) -> None:
    """Test that the mqtt session unauthorized hook is called on unauthorized event."""
    device_manager_kwargs: dict[str, Any] = {}

    def create_device_manager(*args: Any, **kwargs: Any) -> AsyncMock:
        nonlocal device_manager_kwargs
        device_manager_kwargs = kwargs
        return device_manager

    with patch(
        "homeassistant.components.roborock.create_device_manager",
        side_effect=create_device_manager,
    ):
        await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    flows = hass.config_entries.flow.async_progress()
    expect(bool(flows)).to_be(False)

    expect(bool(device_manager_kwargs)).to_be(True)
    mqtt_session_unauthorized_hook = device_manager_kwargs.get(
        "mqtt_session_unauthorized_hook"
    )
    expect(bool(mqtt_session_unauthorized_hook)).to_be(True)
    mqtt_session_unauthorized_hook()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")


@test.cases(
    test.case("old_storage_removed", exists=True, is_dir=True, rmtree_called=True),
    test.case("new_storage_ignored", exists=False, is_dir=False, rmtree_called=False),
    test.case("no_existing_storage", exists=True, is_dir=False, rmtree_called=False),
)
async def remove_old_storage_directory(
    exists: bool,
    is_dir: bool,
    rmtree_called: bool,
    _t: int = Depends(_trigger_executor),
    _platforms: None = Depends(image_platforms_patch),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    storage: pathlib.Path = Depends(storage_path_fixture),
) -> None:
    """Test cleanup of old old map storage."""
    with (
        patch(
            "homeassistant.components.roborock.roborock_storage.Path.exists",
            return_value=exists,
        ),
        patch(
            "homeassistant.components.roborock.roborock_storage.Path.is_dir",
            return_value=is_dir,
        ),
        patch(
            "homeassistant.components.roborock.roborock_storage.shutil.rmtree",
        ) as mock_rmtree,
    ):
        await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    expect(mock_rmtree.called).to_be(rmtree_called)


@test
async def oserror_remove_storage_directory(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(image_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    storage: pathlib.Path = Depends(storage_path_fixture),
) -> None:
    """Test that we gracefully handle failing to remove old map storage."""
    with (
        patch(
            "homeassistant.components.roborock.roborock_storage.Path.exists",
            return_value=True,
        ),
        patch(
            "homeassistant.components.roborock.roborock_storage.Path.is_dir",
            return_value=True,
        ),
        patch(
            "homeassistant.components.roborock.roborock_storage.shutil.rmtree",
            side_effect=OSError,
        ) as mock_rmtree,
    ):
        await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
        await hass.async_block_till_done()
        expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    expect(mock_rmtree.called).to_be(True)


@test
async def not_supported_protocol(
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test that we output a message on incorrect protocol."""
    fake_devices[0].v1_properties = None
    fake_devices[0].zeo = None
    fake_devices[0].dyad = None
    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()
    expect("because its protocol version " in caplog.text).to_be(True)


@test
async def invalid_user_agreement(
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
) -> None:
    """Test that we fail setting up if the user agreement is out of date."""
    with patch(
        "homeassistant.components.roborock.create_device_manager",
        side_effect=RoborockInvalidUserAgreement(),
    ):
        await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
        expect(mock_roborock_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
        expect(mock_roborock_entry.error_reason_translation_key).to_equal(
            "invalid_user_agreement"
        )


@test
async def no_user_agreement(
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
) -> None:
    """Test that we fail setting up if the user has no agreement."""
    with patch(
        "homeassistant.components.roborock.create_device_manager",
        side_effect=RoborockNoUserAgreement(),
    ):
        await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
        expect(mock_roborock_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
        expect(mock_roborock_entry.error_reason_translation_key).to_equal(
            "no_user_agreement"
        )


EXPECTED_ALL_DEVICES = {
    "Roborock S7 MaxV",
    "Roborock S7 MaxV Dock",
    "Roborock S7 2",
    "Roborock S7 2 Dock",
    "Dyad Pro",
    "Zeo One",
    "Roborock Q7",
    "Roborock Q10 S5+",
}


@test
async def stale_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(sensor_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
) -> None:
    """Test that we remove a device if it no longer is given by home_data."""
    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)
    existing_devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_roborock_entry.entry_id
    )
    expect({device.name for device in existing_devices}).to_equal(EXPECTED_ALL_DEVICES)
    fake_devices.pop(0)  # Remove one robot

    await hass.config_entries.async_reload(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()
    new_devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_roborock_entry.entry_id
    )
    expect({device.name for device in new_devices}).to_equal(
        {
            "Roborock S7 2",
            "Roborock S7 2 Dock",
            "Dyad Pro",
            "Zeo One",
            "Roborock Q7",
            "Roborock Q10 S5+",
        }
    )


@test
async def no_stale_device(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(sensor_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
) -> None:
    """Test that we don't remove a device if fails to setup."""
    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)
    existing_devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_roborock_entry.entry_id
    )
    expect({device.name for device in existing_devices}).to_equal(EXPECTED_ALL_DEVICES)

    await hass.config_entries.async_reload(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()
    new_devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_roborock_entry.entry_id
    )
    expect({device.name for device in new_devices}).to_equal(EXPECTED_ALL_DEVICES)


@test
async def migrate_config_entry_unique_id(
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry_data: dict[str, Any] = Depends(config_entry_data_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
) -> None:
    """Test migrating the config entry unique id."""
    # The auto-wired mock_roborock_entry already added the canonical entry to
    # hass. Create a second one with the legacy unique_id (USER_EMAIL) so we
    # can verify that setup rewrites it to the canonical rruid.
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_EMAIL,
        data=config_entry_data,
        version=1,
        minor_version=1,
    )
    # Remove the canonical entry to avoid unique_id conflicts.
    await hass.config_entries.async_remove(mock_roborock_entry.entry_id)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.unique_id).to_equal(ROBOROCK_RRUID)


@test.skip("requires sensor entity_id translation seeding (sensor.roborock_s7_maxv_battery state lookup)")
async def update_unavailability_threshold() -> None:
    """Skipped: depends on entity-id state lookups that need translation seeding."""


@test
async def cloud_api_repair(
    _t: int = Depends(_trigger_executor),
    _no_platforms: None = Depends(no_platforms),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    fake_vacuum: FakeDevice = Depends(fake_vacuum_fixture),
) -> None:
    """Test that a repair is created when we use the cloud api."""
    fake_vacuum.is_connected = True
    fake_vacuum.is_local_connected = False

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()

    issue_registry = ir.async_get(hass)
    expect(len(issue_registry.issues)).to_equal(1)
    expect(
        all(
            issue.translation_key == "cloud_api_used"
            for issue in issue_registry.issues.values()
        )
    ).to_be(True)
    names = {
        issue.translation_placeholders["device_name"]
        for issue in issue_registry.issues.values()
    }
    expect(names).to_equal({"Roborock S7 MaxV"})
    await hass.config_entries.async_unload(mock_roborock_entry.entry_id)

    fake_vacuum.is_local_connected = True

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()

    expect(len(issue_registry.issues)).to_equal(0)


@test.skip("requires sensor entity_id translation seeding (sensor.roborock_s7_maxv_battery state lookup)")
async def cloud_api_repair_cleared_on_update() -> None:
    """Skipped: depends on entity-id state lookups that need translation seeding."""


@test
async def zeo_device_fails_setup(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(sensor_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
) -> None:
    """Simulate an error while setting up a zeo device."""
    zeo_device = next(
        (device for device in fake_devices if device.zeo is not None),
        None,
    )
    expect(zeo_device).not_.to_be(None)
    zeo_device.zeo.query_values.side_effect = RoborockException(
        "Simulated Zeo failure"
    )

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    zeo_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, zeo_device.duid)}
    )
    expect(zeo_device_entry).not_.to_be(None)
    zeo_entities = er.async_entries_for_device(
        entity_registry, zeo_device_entry.id, include_disabled_entities=True
    )
    expect(len(zeo_entities)).to_equal(0)

    all_entities = er.async_entries_for_config_entry(
        entity_registry, mock_roborock_entry.entry_id
    )
    devices_with_entities = {
        device_registry.async_get(entity.device_id).name
        for entity in all_entities
        if entity.device_id is not None
    }
    expect(devices_with_entities).to_equal(
        {
            "Roborock S7 MaxV",
            "Roborock S7 MaxV Dock",
            "Roborock S7 2",
            "Roborock S7 2 Dock",
            "Dyad Pro",
            "Roborock Q7",
            "Roborock Q10 S5+",
        }
    )


@test
async def dyad_device_fails_setup(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(sensor_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
) -> None:
    """Simulate an error while setting up a dyad device."""
    dyad_device = next(
        (device for device in fake_devices if device.dyad is not None),
        None,
    )
    expect(dyad_device).not_.to_be(None)
    dyad_device.dyad.query_values.side_effect = RoborockException(
        "Simulated Dyad failure"
    )

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    dyad_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, dyad_device.duid)}
    )
    expect(dyad_device_entry).not_.to_be(None)
    dyad_entities = er.async_entries_for_device(
        entity_registry, dyad_device_entry.id, include_disabled_entities=True
    )
    expect(len(dyad_entities)).to_equal(0)

    all_entities = er.async_entries_for_config_entry(
        entity_registry, mock_roborock_entry.entry_id
    )
    devices_with_entities = {
        device_registry.async_get(entity.device_id).name
        for entity in all_entities
        if entity.device_id is not None
    }
    expect(devices_with_entities).to_equal(
        {
            "Roborock S7 MaxV",
            "Roborock S7 MaxV Dock",
            "Roborock S7 2",
            "Roborock S7 2 Dock",
            "Zeo One",
            "Roborock Q7",
            "Roborock Q10 S5+",
        }
    )


@test
async def disabled_device_no_coordinator(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(sensor_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
) -> None:
    """Test that a disabled device is registered but no coordinator is created."""
    first_device = fake_devices[0]
    device_registry.async_get_or_create(
        config_entry_id=mock_roborock_entry.entry_id,
        identifiers={(DOMAIN, first_device.duid)},
        name=first_device.device_info.name,
        manufacturer="Roborock",
        disabled_by=dr.DeviceEntryDisabler.USER,
    )

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    disabled_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, first_device.duid)}
    )
    expect(disabled_device_entry).not_.to_be(None)
    expect(disabled_device_entry.disabled).to_be(True)

    coordinators = mock_roborock_entry.runtime_data
    expect(all(coord.duid != first_device.duid for coord in coordinators.v1)).to_be(
        True
    )

    found_devices = device_registry.devices.get_devices_for_config_entry_id(
        mock_roborock_entry.entry_id
    )
    enabled_device_names = {
        device.name for device in found_devices if not device.disabled
    }
    expect("Roborock S7 MaxV" not in enabled_device_names).to_be(True)
    expect("Roborock S7 2" in enabled_device_names).to_be(True)


@test
async def all_devices_disabled(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _platforms: None = Depends(sensor_platforms_patch),
    mock_roborock_entry: MockConfigEntry = Depends(mock_roborock_entry_fixture),
    device_registry: DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: EntityRegistry = Depends(entity_registry_fixture),
    fake_devices: list[FakeDevice] = Depends(fake_devices_fixture),
) -> None:
    """Test that the integration loads successfully when all devices are disabled."""
    for fake_device in fake_devices:
        device_registry.async_get_or_create(
            config_entry_id=mock_roborock_entry.entry_id,
            identifiers={(DOMAIN, fake_device.duid)},
            name=fake_device.device_info.name,
            manufacturer="Roborock",
            disabled_by=dr.DeviceEntryDisabler.USER,
        )

    await hass.config_entries.async_setup(mock_roborock_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_roborock_entry.state).to_be(ConfigEntryState.LOADED)

    all_entities = er.async_entries_for_config_entry(
        entity_registry, mock_roborock_entry.entry_id
    )
    expect(len(all_entities)).to_equal(0)

    for fake_device in fake_devices:
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, fake_device.duid)}
        )
        expect(device_entry).not_.to_be(None)
        expect(device_entry.disabled).to_be(True)
