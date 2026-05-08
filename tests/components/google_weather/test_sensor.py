"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_imperial_units() -> None:
    """Stub for test_sensor_imperial_units."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_update() -> None:
    """Stub for test_state_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def auth_failure_during_update() -> None:
    """Stub for test_auth_failure_during_update."""

