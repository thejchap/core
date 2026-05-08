"""Test Snoo Sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("translation_key not applied; entity ids differ from pytest fixture run")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""
