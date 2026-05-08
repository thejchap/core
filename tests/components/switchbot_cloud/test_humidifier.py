"""Test for the switchbot_cloud humidifiers. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def humidifier() -> None:
    """Stub for test_humidifier (port deferred)."""

@test.skip("syrupy snapshot")
async def humidifier_controller() -> None:
    """Stub for test_humidifier_controller (port deferred)."""

@test.skip("syrupy snapshot")
async def humidifier2_controller() -> None:
    """Stub for test_humidifier2_controller (port deferred)."""
