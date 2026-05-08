"""Tryke skip-stubs for test_cover.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def cover() -> None:
    """Stub for test_cover."""


@test.skip("zha: sibling test pending tryke port")
async def cover_supported_features_runtime_update() -> None:
    """Stub for test_cover_supported_features_runtime_update."""


@test.skip("zha: sibling test pending tryke port")
async def cover_failures() -> None:
    """Stub for test_cover_failures."""
