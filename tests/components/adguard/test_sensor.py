"""Tests for the AdGuard Home sensor entities."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def sensors() -> None:
    """Test the adguard sensor platform."""
