"""Tryke skip-stubs for test_sensor.py - sibling port deferred (304 LOC, 1 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.lacrosse_view.sensor module imports cleanly."""
    from homeassistant.components.lacrosse_view import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def entities_added() -> None:
    """Stub for test_entities_added."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def sensor_permission() -> None:
    """Stub for test_sensor_permission."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def field_not_supported() -> None:
    """Stub for test_field_not_supported."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def field_types() -> None:
    """Stub for test_field_types."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def no_field() -> None:
    """Stub for test_no_field."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def field_data_missing() -> None:
    """Stub for test_field_data_missing."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def no_readings() -> None:
    """Stub for test_no_readings."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def mixed_readings() -> None:
    """Stub for test_mixed_readings."""

@test.skip("sibling port deferred (304 LOC, 1 parametrize)")
async def other_error() -> None:
    """Stub for test_other_error."""
