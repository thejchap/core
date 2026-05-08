"""Tryke skip stubs for test_diagnostics - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entry_diagnostics() -> None:
    """Stub for test_entry_diagnostics (port deferred)."""


