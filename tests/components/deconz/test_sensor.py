"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("snapshot test - port deferred")
async def not_allow_clip_sensor() -> None:
    """Stub for test_not_allow_clip_sensor (port deferred)."""

@test.skip("snapshot test - port deferred")
async def allow_clip_sensors() -> None:
    """Stub for test_allow_clip_sensors (port deferred)."""

@test.skip("snapshot test - port deferred")
async def add_new_sensor() -> None:
    """Stub for test_add_new_sensor (port deferred)."""

@test.skip("snapshot test - port deferred")
async def dont_add_sensor_if_state_is_none() -> None:
    """Stub for test_dont_add_sensor_if_state_is_none (port deferred)."""

@test.skip("snapshot test - port deferred")
async def air_quality_sensor_without_ppb() -> None:
    """Stub for test_air_quality_sensor_without_ppb (port deferred)."""

@test.skip("snapshot test - port deferred")
async def add_battery_later() -> None:
    """Stub for test_add_battery_later (port deferred)."""

@test.skip("snapshot test - port deferred")
async def special_danfoss_battery_creation() -> None:
    """Stub for test_special_danfoss_battery_creation (port deferred)."""

@test.skip("snapshot test - port deferred")
async def unsupported_sensor() -> None:
    """Stub for test_unsupported_sensor (port deferred)."""
