"""Tryke skip-stubs for test_sensor_v1.py - large file (631 LOC) - port deferred."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.hue module imports cleanly."""
    from homeassistant.components import hue  # noqa: PLC0415
    expect(hue).not_.to_be(None)


@test.skip("large file (631 LOC) - port deferred")
async def no_sensors() -> None:
    """Stub for test_no_sensors."""

@test.skip("large file (631 LOC) - port deferred")
async def sensors_with_multiple_bridges() -> None:
    """Stub for test_sensors_with_multiple_bridges."""

@test.skip("large file (631 LOC) - port deferred")
async def sensors() -> None:
    """Stub for test_sensors."""

@test.skip("large file (631 LOC) - port deferred")
async def unsupported_sensors() -> None:
    """Stub for test_unsupported_sensors."""

@test.skip("large file (631 LOC) - port deferred")
async def new_sensor_discovered() -> None:
    """Stub for test_new_sensor_discovered."""

@test.skip("large file (631 LOC) - port deferred")
async def sensor_removed() -> None:
    """Stub for test_sensor_removed."""

@test.skip("large file (631 LOC) - port deferred")
async def update_timeout() -> None:
    """Stub for test_update_timeout."""

@test.skip("large file (631 LOC) - port deferred")
async def update_unauthorized() -> None:
    """Stub for test_update_unauthorized."""

@test.skip("large file (631 LOC) - port deferred")
async def hue_events() -> None:
    """Stub for test_hue_events."""
