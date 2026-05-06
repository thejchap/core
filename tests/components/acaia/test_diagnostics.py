"""Tests for the diagnostics data provided by the Acaia integration."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def diagnostics() -> None:
    """Test diagnostics (snapshot)."""
