"""Tryke skip stub for test_device_tracker.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def router_mode() -> None:
    """Stub for test_router_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def bridge_mode() -> None:
    """Stub for test_bridge_mode."""

