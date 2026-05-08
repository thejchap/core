"""Tryke skip-stubs for test_device_trigger.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def event_button_press() -> None:
    """Stub for test_event_button_press."""


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
