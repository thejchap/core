"""Tryke skip stub for test_websocket_api.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("thread: sibling test pending tryke port — needs: ws client")
async def websocket_api() -> None:
    """Placeholder skipped sibling tests."""
