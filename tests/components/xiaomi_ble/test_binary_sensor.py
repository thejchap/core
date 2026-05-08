"""Tryke skip-stubs for test_binary_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def door_problem_sensors() -> None:
    """Stub for test_door_problem_sensors."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def light_motion() -> None:
    """Stub for test_light_motion."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def moisture() -> None:
    """Stub for test_moisture."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def opening() -> None:
    """Stub for test_opening."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def opening_problem_sensors() -> None:
    """Stub for test_opening_problem_sensors."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def smoke() -> None:
    """Stub for test_smoke."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def power() -> None:
    """Stub for test_power."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def unavailable() -> None:
    """Stub for test_unavailable."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device() -> None:
    """Stub for test_sleepy_device."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sleepy_device_restore_state() -> None:
    """Stub for test_sleepy_device_restore_state."""
