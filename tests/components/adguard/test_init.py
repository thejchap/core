"""Tests for the AdGuard Home."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures (init_integration, mock_config_entry, mock_adguard) need _fixtures.py port")
async def setup() -> None:
    """Test the adguard setup."""


@test.skip("conftest fixtures need _fixtures.py port")
async def setup_failed() -> None:
    """Test the adguard setup failed."""
