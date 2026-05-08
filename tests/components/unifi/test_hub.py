"""Tryke skip stub for test_hub.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("unifi: sibling test pending tryke port — needs: aioclient_mock")
async def hub() -> None:
    """Placeholder skipped sibling tests."""
