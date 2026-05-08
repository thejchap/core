"""Tests for the Smarty button platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def all_entities() -> None:
    """Stub for test_all_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def setting_value() -> None:
    """Stub for test_setting_value (port deferred)."""
