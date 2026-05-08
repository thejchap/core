"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def services() -> None:
    """Stub for test_services."""

