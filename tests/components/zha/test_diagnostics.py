"""Tryke skip-stubs for test_diagnostics.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def diagnostics_for_config_entry() -> None:
    """Stub for test_diagnostics_for_config_entry."""


@test.skip("zha: sibling test pending tryke port")
async def diagnostics_for_device() -> None:
    """Stub for test_diagnostics_for_device."""
