"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def connection_error() -> None:
    """Stub for test_connection_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def add_remove_entities() -> None:
    """Stub for test_add_remove_entities."""

