"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_none_values() -> None:
    """Stub for test_sensor_none_values."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def readings_connection_error_makes_unavailable() -> None:
    """Stub for test_readings_connection_error_makes_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_reappears_after_removal() -> None:
    """Stub for test_device_reappears_after_removal."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dynamic_device_added() -> None:
    """Stub for test_dynamic_device_added."""

