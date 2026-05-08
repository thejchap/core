"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_actions() -> None:
    """Stub for test_switch_actions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_switch_found() -> None:
    """Stub for test_no_switch_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def error_flipr_api() -> None:
    """Stub for test_error_flipr_api."""

