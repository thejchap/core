"""Tryke skip stub for test_select.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_actions() -> None:
    """Stub for test_select_actions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_select_found() -> None:
    """Stub for test_no_select_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def error_flipr_api() -> None:
    """Stub for test_error_flipr_api."""

