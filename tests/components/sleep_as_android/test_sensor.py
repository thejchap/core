"""Test the Sleep as Android sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def webhook_sensor() -> None:
    """Stub for test_webhook_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def webhook_sensor_alarm_unset() -> None:
    """Stub for test_webhook_sensor_alarm_unset (port deferred)."""
