"""Test the Anthem A/V Receivers media_player."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures (init_integration, mock_anthemav, update_callback) need _fixtures.py port")
async def zones_loaded() -> None:
    """Test zones are loaded."""


@test.skip("conftest fixtures need _fixtures.py port")
async def update_states_zone1() -> None:
    """Test zone states are updated."""
