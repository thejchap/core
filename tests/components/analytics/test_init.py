"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("pending tryke port")
async def labs_feature_toggle() -> None:
    """Stub for test_labs_feature_toggle (port deferred)."""

@test.skip("pending tryke port")
async def websocket() -> None:
    """Stub for test_websocket (port deferred)."""
