"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_positions_service() -> None:
    """Stub for test_get_positions_service."""

