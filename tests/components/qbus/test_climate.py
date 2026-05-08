"""Test Qbus light entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("mqtt_mock not in shim")
async def climate() -> None:
    """Stub for test_climate (port deferred)."""

@test.skip("mqtt_mock not in shim")
async def climate_when_invalid_state_received() -> None:
    """Stub for test_climate_when_invalid_state_received (port deferred)."""

@test.skip("mqtt_mock not in shim")
async def climate_with_fast_subsequent_changes() -> None:
    """Stub for test_climate_with_fast_subsequent_changes (port deferred)."""

@test.skip("mqtt_mock not in shim")
async def climate_with_unknown_preset() -> None:
    """Stub for test_climate_with_unknown_preset (port deferred)."""
