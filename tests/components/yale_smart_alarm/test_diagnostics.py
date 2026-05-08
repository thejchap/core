"""Tryke skip-stubs for test_diagnostics.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs syrupy snapshot, hass_client, load_config_entry")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""
