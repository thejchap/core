"""Tests for the AdGuard Home update entity."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def update_snapshot() -> None:
    """Test the adguard update platform (snapshot)."""


@test.skip("conftest fixtures need _fixtures.py port")
async def update_disabled() -> None:
    """Test the adguard update is disabled."""


@test.skip("conftest fixtures need _fixtures.py port")
async def update_install() -> None:
    """Test the adguard update installation."""


@test.skip("conftest fixtures need _fixtures.py port")
async def update_install_failed() -> None:
    """Test the adguard update install failed."""
