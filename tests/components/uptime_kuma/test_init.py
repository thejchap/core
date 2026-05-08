"""Tryke skip stub for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uptime_kuma: sibling test pending tryke port — needs: ws client")
async def init() -> None:
    """Placeholder skipped sibling tests."""
