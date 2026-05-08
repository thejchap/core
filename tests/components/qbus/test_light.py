"""Test Qbus light entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("mqtt_mock not in shim")
async def light() -> None:
    """Stub for test_light (port deferred)."""

@test.skip("mqtt_mock not in shim")
async def light_ignore_missing_percentage() -> None:
    """Stub for test_light_ignore_missing_percentage (port deferred)."""
