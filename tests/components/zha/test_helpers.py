"""Tryke skip-stubs for test_helpers.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def zcl_schema_conversions() -> None:
    """Stub for test_zcl_schema_conversions."""


@test.skip("zha: sibling test pending tryke port")
async def exclude_none_values() -> None:
    """Stub for test_exclude_none_values."""


@test.skip("zha: sibling test pending tryke port")
async def create_zha_config_remove_unused() -> None:
    """Stub for test_create_zha_config_remove_unused."""
