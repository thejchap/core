"""Tryke skip-stubs for test_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def sensors() -> None:
    """Stub for test_sensors."""


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
