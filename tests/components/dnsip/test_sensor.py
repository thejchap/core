"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def legacy_sensor() -> None:
    """Stub for test_legacy_sensor."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensor_no_response() -> None:
    """Stub for test_sensor_no_response."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def sensor_timeout() -> None:
    """Stub for test_sensor_timeout."""

