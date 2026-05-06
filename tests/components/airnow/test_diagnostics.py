"""Test AirNow diagnostics."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot and hass_client")
async def entry_diagnostics() -> None:
    """Test config entry diagnostics."""
