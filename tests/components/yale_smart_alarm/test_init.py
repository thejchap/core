"""Tryke skip-stubs for test_init.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs get_client conftest fixture")
async def setup_entry() -> None:
    """Stub for test_setup_entry."""


@test.skip("yale_smart_alarm: needs get_client conftest fixture")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry."""
