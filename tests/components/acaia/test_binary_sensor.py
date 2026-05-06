"""Test binary sensors for acaia integration."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def binary_sensors() -> None:
    """Test the acaia binary sensors (snapshot platform)."""
