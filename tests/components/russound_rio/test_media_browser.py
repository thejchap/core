"""Tests for the Russound RIO media browser. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def browse_media_root() -> None:
    """Stub for test_browse_media_root (port deferred)."""

@test.skip("syrupy snapshot")
async def browse_presets() -> None:
    """Stub for test_browse_presets (port deferred)."""
