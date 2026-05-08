"""Tryke skip stub for test_media_source.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("synology_dsm: sibling test pending tryke port — needs: complex parametrize")
async def media_source() -> None:
    """Placeholder skipped sibling tests."""
