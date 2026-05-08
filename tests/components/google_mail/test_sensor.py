"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_reauth_trigger() -> None:
    """Stub for test_sensor_reauth_trigger."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_token_error_no_reauth() -> None:
    """Stub for test_sensor_token_error_no_reauth."""

