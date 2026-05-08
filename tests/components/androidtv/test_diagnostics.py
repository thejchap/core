"""Tryke skip stub for test_diagnostics.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""

