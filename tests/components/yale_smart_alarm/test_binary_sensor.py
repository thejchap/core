"""Tryke skip-stubs for test_binary_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor."""
