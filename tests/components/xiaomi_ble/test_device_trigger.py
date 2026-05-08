"""Test Xiaomi BLE events (tryke port)."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.xiaomi_ble.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import make_advertisement
from .conftest import MockBleakClientBattery5

from tests.common import MockConfigEntry, async_capture_events
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
async def event_button_press(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Make sure that a button press event is fired."""
    mac = "54:EF:44:E3:9C:BC"
    data = {"bindkey": "5b51a7c91cde6707c9ef18dfda143a58"}
    entry = MockConfigEntry(domain=DOMAIN, unique_id=mac, data=data)
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    events = async_capture_events(hass, "xiaomi_ble_event")

    # Emit button press event
    inject_bluetooth_service_info_bleak(
        hass,
        make_advertisement(
            mac,
            b'XY\x97\td\xbc\x9c\xe3D\xefT" `\x88\xfd\x00\x00\x00\x00:\x14\x8f\xb3',
        ),
    )

    # wait for the event
    await hass.async_block_till_done()
    expect(len(events)).to_be(1)
    expect(events[0].data["address"]).to_equal("54:EF:44:E3:9C:BC")
    expect(events[0].data["event_type"]).to_equal("press")
    expect(events[0].data["event_properties"]).to_be(None)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def event_unlock_outside_the_door() -> None:
    """Stub for test_event_unlock_outside_the_door."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def event_successful_fingerprint_match_the_door() -> None:
    """Stub for test_event_successful_fingerprint_match_the_door."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def event_motion_detected() -> None:
    """Stub for test_event_motion_detected."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def event_dimmer_rotate() -> None:
    """Stub for test_event_dimmer_rotate."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def get_triggers_button() -> None:
    """Stub for test_get_triggers_button."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def get_triggers_double_button() -> None:
    """Stub for test_get_triggers_double_button."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def get_triggers_lock() -> None:
    """Stub for test_get_triggers_lock."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def get_triggers_motion() -> None:
    """Stub for test_get_triggers_motion."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def get_triggers_for_invalid_xiami_ble_device() -> None:
    """Stub for test_get_triggers_for_invalid_xiami_ble_device."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def get_triggers_for_invalid_device_id() -> None:
    """Stub for test_get_triggers_for_invalid_device_id."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def if_fires_on_button_press() -> None:
    """Stub for test_if_fires_on_button_press."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def if_fires_on_double_button_long_press() -> None:
    """Stub for test_if_fires_on_double_button_long_press."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def if_fires_on_motion_detected() -> None:
    """Stub for test_if_fires_on_motion_detected."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def automation_with_invalid_trigger_type() -> None:
    """Stub for test_automation_with_invalid_trigger_type."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def automation_with_invalid_trigger_event_property() -> None:
    """Stub for test_automation_with_invalid_trigger_event_property."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def triggers_for_invalid__model() -> None:
    """Stub for test_triggers_for_invalid__model."""
