"""Test Adax sensor entity."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("uses syrupy snapshot")
async def sensor_cloud() -> None:
    """Test sensor setup for cloud connection."""


@test.skip("conftest fixtures need _fixtures.py port")
async def sensor_local_not_created() -> None:
    """Test that sensors are not created for local connection."""


@test.skip("uses syrupy snapshot")
async def multiple_devices_create_individual_sensors() -> None:
    """Test that multiple devices create individual sensors."""


@test.skip("uses syrupy snapshot")
async def fallback_to_get_rooms() -> None:
    """Test fallback to get_rooms when fetch_rooms_info returns empty list."""
