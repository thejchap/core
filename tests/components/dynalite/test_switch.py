"""Tryke skip stubs for test_switch - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_setup() -> None:
    """Stub for test_switch_setup (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_restore_state() -> None:
    """Stub for test_switch_restore_state (port deferred)."""


