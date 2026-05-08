"""Tryke skip stub for test_sip.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("voip: sibling test pending tryke port")
async def sip() -> None:
    """Placeholder skipped sibling tests."""
