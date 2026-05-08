"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_vacation() -> None:
    """Stub for test_set_vacation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reauth_trigger() -> None:
    """Stub for test_reauth_trigger."""

