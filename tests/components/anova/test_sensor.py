"""Test the Anova sensors."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures (anova_api, anova_api_no_data) need _fixtures.py port")
async def sensors() -> None:
    """Test setting up creates the sensors."""


@test.skip("conftest fixtures need _fixtures.py port")
async def no_data_sensors() -> None:
    """Test that if we have no data for the device, and we have not set it up previously, It is not immediately set up."""
