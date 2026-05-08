"""Test schlage sensor. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("mock_added_config_entry includes mock_setup_entry; sensor not created")
async def battery_sensor() -> None:
    """Stub for test_battery_sensor (port deferred)."""
