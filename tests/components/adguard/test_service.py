"""Tests for the AdGuard Home services."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures (init_integration, mock_adguard) need _fixtures.py port")
async def service_registration() -> None:
    """Test the adguard services be registered."""


@test.skip("conftest fixtures need _fixtures.py port")
async def service() -> None:
    """Test the adguard services be unregistered with unloading last entry."""
