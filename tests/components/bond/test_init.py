"""Tests for the Bond module."""

from typing import Any
from unittest.mock import MagicMock, Mock

from aiohttp import ClientConnectionError, ClientResponseError
from bond_async import DeviceType
from tryke import Depends, expect, fixture, test

from homeassistant.components.bond import DOMAIN, BondData
from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ASSUMED_STATE, CONF_ACCESS_TOKEN, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.setup import async_setup_component

from .common import (
    ceiling_fan,
    patch_bond_bridge,
    patch_bond_device,
    patch_bond_device_ids,
    patch_bond_device_properties,
    patch_bond_device_state,
    patch_bond_version,
    patch_setup_entry,
    patch_start_bpup,
    setup_bond_entity,
    setup_platform,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    area_registry as area_registry_fx,
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    hass_ws_client as hass_ws_client_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def async_setup_no_domain_config(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test setup without configuration is noop."""
    result = await async_setup_component(hass, DOMAIN, {})

    expect(result).to_be(True)


@test.cases(
    test.case("client_connection_error", exc=ClientConnectionError),
    test.case("timeout_error", exc=TimeoutError),
    test.case("os_error", exc=OSError),
)
async def async_setup_raises_entry_not_ready(
    exc: type[Exception],
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )
    config_entry.add_to_hass(hass)

    with patch_bond_version(side_effect=exc):
        await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_setup_raises_entry_not_ready_client_response_error(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test ConfigEntryNotReady when ClientResponseError 404 occurs during setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )
    config_entry.add_to_hass(hass)

    exc = ClientResponseError(MagicMock(), MagicMock(), status=404)
    with patch_bond_version(side_effect=exc):
        await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_setup_raises_fails_if_auth_fails(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test that setup fails if auth fails during setup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )
    config_entry.add_to_hass(hass)

    with patch_bond_version(
        side_effect=ClientResponseError(MagicMock(), MagicMock(), status=401)
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def async_setup_entry_sets_up_hub_and_supported_domains(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test that configuring entry sets up cover domain."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    with (
        patch_bond_bridge(),
        patch_bond_version(
            return_value={
                "bondid": "ZXXX12345",
                "target": "test-model",
                "fw_ver": "test-version",
                "mcu_ver": "test-hw-version",
            }
        ),
        patch_setup_entry("cover") as mock_cover_async_setup_entry,
        patch_setup_entry("fan") as mock_fan_async_setup_entry,
        patch_setup_entry("light") as mock_light_async_setup_entry,
        patch_setup_entry("switch") as mock_switch_async_setup_entry,
    ):
        result = await setup_bond_entity(hass, config_entry, patch_device_ids=True)
        expect(result).to_be(True)
        await hass.async_block_till_done()

    expect(isinstance(config_entry.runtime_data, BondData)).to_be(True)
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.unique_id).to_equal("ZXXX12345")

    hub = device_registry.async_get_device(identifiers={(DOMAIN, "ZXXX12345")})
    expect(hub.name).to_equal("bond-name")
    expect(hub.manufacturer).to_equal("Olibra")
    expect(hub.model).to_equal("test-model")
    expect(hub.sw_version).to_equal("test-version")
    expect(hub.hw_version).to_equal("test-hw-version")
    expect(hub.configuration_url).to_equal("http://some host")

    expect(len(mock_cover_async_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_fan_async_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_light_async_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_switch_async_setup_entry.mock_calls)).to_equal(1)


@test
async def unload_config_entry(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test that configuration entry supports unloading."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    result = await setup_bond_entity(
        hass,
        config_entry,
        patch_version=True,
        patch_device_ids=True,
        patch_platforms=True,
        patch_bridge=True,
    )
    expect(result).to_be(True)
    await hass.async_block_till_done()

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def old_identifiers_are_removed(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test we remove the old non-unique identifiers."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )
    config_entry.add_to_hass(hass)

    old_identifers = (DOMAIN, "device_id")
    new_identifiers = (DOMAIN, "ZXXX12345", "device_id")
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={old_identifers},
        manufacturer="any",
        name="old",
    )

    with (
        patch_bond_bridge(),
        patch_bond_version(
            return_value={
                "bondid": "ZXXX12345",
                "target": "test-model",
                "fw_ver": "test-version",
            }
        ),
        patch_start_bpup(),
        patch_bond_device_ids(return_value=["bond-device-id", "device_id"]),
        patch_bond_device(
            return_value={
                "name": "test1",
                "type": DeviceType.GENERIC_DEVICE,
            }
        ),
        patch_bond_device_properties(return_value={}),
        patch_bond_device_state(return_value={}),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.unique_id).to_equal("ZXXX12345")

    expect(device_registry.async_get_device(identifiers={old_identifers})).to_be(None)
    expect(
        device_registry.async_get_device(identifiers={new_identifiers}) is not None
    ).to_be(True)


@test
async def smart_by_bond_device_suggested_area(
    hass: HomeAssistant = Depends(hass_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test we can setup a smart by bond device and get the suggested area."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    config_entry.add_to_hass(hass)

    with (
        patch_bond_bridge(side_effect=ClientResponseError(Mock(), Mock(), status=404)),
        patch_bond_version(
            return_value={
                "bondid": "KXXX12345",
                "target": "test-model",
                "fw_ver": "test-version",
            }
        ),
        patch_start_bpup(),
        patch_bond_device_ids(return_value=["bond-device-id", "device_id"]),
        patch_bond_device(
            return_value={
                "name": "test1",
                "type": DeviceType.GENERIC_DEVICE,
                "location": "Den",
            }
        ),
        patch_bond_device_properties(return_value={}),
        patch_bond_device_state(return_value={}),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.unique_id).to_equal("KXXX12345")

    device = device_registry.async_get_device(identifiers={(DOMAIN, "KXXX12345")})
    expect(device is not None).to_be(True)
    expect(device.area_id).to_equal(area_registry.async_get_area_by_name("Den").id)


@test
async def bridge_device_suggested_area(
    hass: HomeAssistant = Depends(hass_fx),
    area_registry: ar.AreaRegistry = Depends(area_registry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test we can setup a bridge bond device and get the suggested area."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    )

    config_entry.add_to_hass(hass)

    with (
        patch_bond_bridge(
            return_value={
                "name": "Office Bridge",
                "location": "Office",
            }
        ),
        patch_bond_version(
            return_value={
                "bondid": "ZXXX12345",
                "target": "test-model",
                "fw_ver": "test-version",
            }
        ),
        patch_start_bpup(),
        patch_bond_device_ids(return_value=["bond-device-id", "device_id"]),
        patch_bond_device(
            return_value={
                "name": "test1",
                "type": DeviceType.GENERIC_DEVICE,
                "location": "Bathroom",
            }
        ),
        patch_bond_device_properties(return_value={}),
        patch_bond_device_state(return_value={}),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.unique_id).to_equal("ZXXX12345")

    device = device_registry.async_get_device(identifiers={(DOMAIN, "ZXXX12345")})
    expect(device is not None).to_be(True)
    expect(device.area_id).to_equal(area_registry.async_get_area_by_name("Office").id)


@test
async def device_remove_devices(
    hass: HomeAssistant = Depends(hass_fx),
    hass_ws_client: Any = Depends(hass_ws_client_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
) -> None:
    """Test we can only remove a device that no longer exists."""
    expect(await async_setup_component(hass, "config", {})).to_be(True)

    config_entry = await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_version={"bondid": "test-hub-id"},
        bond_device_id="test-device-id",
    )

    entity = entity_registry.entities["fan.name_1"]
    expect(entity.unique_id).to_equal("test-hub-id_test-device-id")

    device_entry = device_registry.async_get(entity.device_id)
    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(False)

    dead_device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "test-hub-id", "remove-device-id")},
    )
    response = await client.remove_device(dead_device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(True)

    dead_device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "wrong-hub-id", "test-device-id")},
    )
    response = await client.remove_device(dead_device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(True)

    hub_device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "test-hub-id")},
    )
    response = await client.remove_device(hub_device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(False)


@test
async def smart_by_bond_v3_firmware(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test we can detect smart by bond with the v3 firmware."""
    await setup_platform(
        hass,
        FAN_DOMAIN,
        ceiling_fan("name-1"),
        bond_version={"bondid": "KXXXX12345", "target": "breck-northstar"},
        bond_device_id="test-device-id",
    )
    expect(
        ATTR_ASSUMED_STATE not in hass.states.get("fan.name_1").attributes
    ).to_be(True)
