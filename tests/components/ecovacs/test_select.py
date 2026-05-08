"""Tryke skip stub for test_select.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def selects() -> None:
    """Stub for test_selects."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def selects_change() -> None:
    """Stub for test_selects_change."""

