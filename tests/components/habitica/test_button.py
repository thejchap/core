"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_press() -> None:
    """Stub for test_button_press."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_press_exceptions() -> None:
    """Stub for test_button_press_exceptions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_unavailable() -> None:
    """Stub for test_button_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def class_change() -> None:
    """Stub for test_class_change."""

