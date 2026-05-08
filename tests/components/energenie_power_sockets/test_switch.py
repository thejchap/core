"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_setup() -> None:
    """Stub for test_switch_setup."""

