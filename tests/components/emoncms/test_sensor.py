"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_feed_selected() -> None:
    """Stub for test_no_feed_selected."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_feed_broadcast() -> None:
    """Stub for test_no_feed_broadcast."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update() -> None:
    """Stub for test_coordinator_update."""

