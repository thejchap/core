"""Test the Fjäråskupan integration init."""

from fjaraskupan import ANNOUNCE_MANUFACTURER, DEVICE_NAME
from habluetooth import BluetoothServiceInfo
from tryke import Depends, expect, fixture, test

from homeassistant.components.fjaraskupan.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.components.bluetooth import (
    inject_bluetooth_service_info,
    patch_discovered_devices,
)
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    hass_ws_client,
    mock_network,
)

MOCK_SERVICE_INFO = BluetoothServiceInfo(
    address="11:11:11:11:11:11",
    name=DEVICE_NAME,
    service_uuids=[],
    rssi=-60,
    manufacturer_data={ANNOUNCE_MANUFACTURER: b"ODFJAR\x01\x02\x00\x00\x00\x30\x04"},
    service_data={},
    source="local",
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def setup(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup creates expected device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    inject_bluetooth_service_info(
        hass,
        MOCK_SERVICE_INFO,
    )

    await hass.async_block_till_done()
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERVICE_INFO.address)}
    )
    expect(device_entry).not_.to_be(None)
    expect(device_entry.manufacturer).to_equal("Fjäråskupan")
    expect(device_entry.name).to_equal("Fjäråskupan")


@test
async def remove_device(
    _trigger: None = Depends(_trigger_executor),
    _bluetooth: None = Depends(enable_bluetooth),
    hass: HomeAssistant = Depends(hass_fixture),
    ws_client_factory=Depends(hass_ws_client),
) -> None:
    """Test we can remove devices that are not available."""
    expect(await async_setup_component(hass, "config", {})).to_be(True)

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    inject_bluetooth_service_info(hass, MOCK_SERVICE_INFO)

    await hass.async_block_till_done()
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERVICE_INFO.address)}
    )
    expect(device_entry).not_.to_be(None)

    client = await ws_client_factory()
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    expect(response["success"]).to_be(False)

    await hass.async_block_till_done()
    expect(device_registry.async_get(device_entry.id)).not_.to_be(None)

    with patch_discovered_devices([]):
        response = await client.remove_device(device_entry.id, config_entry.entry_id)
        expect(response["success"]).to_be(True)

        await hass.async_block_till_done()
        expect(device_registry.async_get(device_entry.id)).to_be(None)
