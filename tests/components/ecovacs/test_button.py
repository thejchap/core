"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def disabled_by_default_buttons() -> None:
    """Stub for test_disabled_by_default_buttons."""

