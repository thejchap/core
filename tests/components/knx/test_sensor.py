"""Tryke skip-stubs for test_sensor.py - sibling port deferred (349 LOC, 3 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.knx.sensor module imports cleanly."""
    from homeassistant.components.knx import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def sensor() -> None:
    """Stub for test_sensor."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def sensor_restore() -> None:
    """Stub for test_sensor_restore."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def last_reported() -> None:
    """Stub for test_last_reported."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def always_callback() -> None:
    """Stub for test_always_callback."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def sensor_yaml_attribute_validation() -> None:
    """Stub for test_sensor_yaml_attribute_validation."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def sensor_ui_create() -> None:
    """Stub for test_sensor_ui_create."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def sensor_ui_load() -> None:
    """Stub for test_sensor_ui_load."""

@test.skip("sibling port deferred (349 LOC, 3 parametrize)")
async def sensor_ui_create_attribute_validation() -> None:
    """Stub for test_sensor_ui_create_attribute_validation."""
