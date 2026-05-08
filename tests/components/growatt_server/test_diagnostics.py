"""Tryke skip stub for test_diagnostics.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostics_classic_api() -> None:
    """Stub for test_diagnostics_classic_api."""

