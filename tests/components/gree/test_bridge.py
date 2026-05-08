"""Tryke skip stub for test_bridge.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_after_setup() -> None:
    """Stub for test_discovery_after_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_updates() -> None:
    """Stub for test_coordinator_updates."""

