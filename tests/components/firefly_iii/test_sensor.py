"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def refresh_exceptions() -> None:
    """Stub for test_refresh_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def budget_sensor_updates_after_refresh() -> None:
    """Stub for test_budget_sensor_updates_after_refresh."""

