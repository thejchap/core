"""Test the Anthem A/V Receivers init."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures (mock_connection_create, mock_anthemav, init_integration, update_callback) need _fixtures.py port")
async def load_unload_config_entry() -> None:
    """Test load and unload AnthemAv component."""


@test.skip("conftest fixtures need _fixtures.py port")
async def config_entry_not_ready_when_oserror() -> None:
    """Test AnthemAV configuration entry not ready."""


@test.skip("conftest fixtures need _fixtures.py port")
async def anthemav_dispatcher_signal() -> None:
    """Test send update signal to dispatcher."""
