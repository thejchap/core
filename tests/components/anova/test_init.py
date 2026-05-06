"""Test init for Anova."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures (anova_api, anova_api_wrong_login, anova_api_no_devices, anova_api_websocket_failure) need _fixtures.py port")
async def async_setup_entry() -> None:
    """Test a successful setup entry."""


@test.skip("conftest fixtures need _fixtures.py port")
async def wrong_login() -> None:
    """Test for setup failure if connection to Anova is missing."""


@test.skip("conftest fixtures need _fixtures.py port")
async def unload_entry() -> None:
    """Test successful unload of entry."""


@test.skip("conftest fixtures need _fixtures.py port")
async def no_devices_found() -> None:
    """Test when there don't seem to be any devices on the account."""


@test.skip("conftest fixtures need _fixtures.py port")
async def websocket_failure() -> None:
    """Test that we successfully handle a websocket failure on setup."""


@test.skip("conftest fixtures need _fixtures.py port")
async def migration_removing_devices_in_config_entry() -> None:
    """Test a successful setup entry."""
