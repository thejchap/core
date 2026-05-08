"""Tests for the Slide Local button platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def pressing_button() -> None:
    """Stub for test_pressing_button (port deferred)."""

@test.skip("syrupy snapshot")
async def pressing_button_exception() -> None:
    """Stub for test_pressing_button_exception (port deferred)."""
