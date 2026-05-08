"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_disabled_by_default() -> None:
    """Stub for test_sensors_disabled_by_default."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_unknown_status() -> None:
    """Stub for test_sensors_unknown_status."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_active_error_and_alert() -> None:
    """Stub for test_sensors_active_error_and_alert."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_conditional_creation() -> None:
    """Stub for test_sensors_conditional_creation."""

