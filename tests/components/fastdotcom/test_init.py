"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def delayed_speedtest_during_startup() -> None:
    """Stub for test_delayed_speedtest_during_startup."""

