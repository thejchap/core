"""Tests for the AdGuard Home switch entity."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def switch_snapshot() -> None:
    """Test the adguard switch platform (snapshot)."""


@test.skip("conftest fixtures (init_integration, mock_adguard) need _fixtures.py port")
async def switch_actions() -> None:
    """Test the adguard switch actions."""


@test.skip("conftest fixtures need _fixtures.py port")
async def switch_action_failed() -> None:
    """Test the adguard switch actions."""
