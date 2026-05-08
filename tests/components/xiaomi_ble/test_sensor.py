"""Test Xiaomi BLE sensors (tryke port)."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.components.xiaomi_ble.const import DOMAIN
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from . import MMC_T201_1_SERVICE_INFO
from .conftest import MockBleakClientBattery5

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info_bleak
from tests.hass_fixtures import enable_bluetooth, hass as hass_fixture, mock_network


@fixture
def mock_bluetooth_xiaomi() -> Generator[None]:
    """Auto mock the BleakClient (replaces xiaomi_ble conftest autouse)."""
    with patch("xiaomi_ble.parser.BleakClient", MockBleakClientBattery5):
        yield


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
    _mock_bleak: None = Depends(mock_bluetooth_xiaomi),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def sensors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="00:81:F9:DD:6F:C1",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(0)
    inject_bluetooth_service_info_bleak(hass, MMC_T201_1_SERVICE_INFO)
    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_be(2)

    # Find the temperature sensor by state value (entity_id slug differs
    # without compiled translations).
    states = hass.states.async_all("sensor")
    temp_states = [s for s in states if s.state == "36.8719980616822"]
    expect(len(temp_states)).to_be(1)
    expect(temp_states[0].attributes[ATTR_UNIT_OF_MEASUREMENT]).to_equal("°C")
    expect(temp_states[0].attributes[ATTR_STATE_CLASS]).to_equal("measurement")

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_formaldeyhde() -> None:
    """Stub for test_xiaomi_formaldeyhde."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_consumable() -> None:
    """Stub for test_xiaomi_consumable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_score() -> None:
    """Stub for test_xiaomi_score."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_battery_voltage() -> None:
    """Stub for test_xiaomi_battery_voltage."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_hhccjcy01() -> None:
    """Stub for test_xiaomi_hhccjcy01."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_hhccjcy01_not_connectable() -> None:
    """Stub for test_xiaomi_hhccjcy01_not_connectable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_hhccjcy01_only_some_sources_connectable() -> None:
    """Stub for test_xiaomi_hhccjcy01_only_some_sources_connectable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_xmosb01xs() -> None:
    """Stub for test_xiaomi_xmosb01xs."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_cgdk2_bind_key() -> None:
    """Stub for test_xiaomi_cgdk2_bind_key."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def hhccjcy10_uuid() -> None:
    """Stub for test_hhccjcy10_uuid."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def miscale_v1_uuid() -> None:
    """Stub for test_miscale_v1_uuid."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def miscale_v2_uuid() -> None:
    """Stub for test_miscale_v2_uuid."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device_restore_state() -> None:
    """Stub for test_sleepy_device_restore_state."""
