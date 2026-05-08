"""Tests for SMLIGHT light entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def light_setup_ultima() -> None:
    """Stub for test_light_setup_ultima (port deferred)."""

@test.skip("syrupy snapshot")
async def light_not_created_non_ultima() -> None:
    """Stub for test_light_not_created_non_ultima (port deferred)."""

@test.skip("syrupy snapshot")
async def light_turn_on_off() -> None:
    """Stub for test_light_turn_on_off (port deferred)."""

@test.skip("syrupy snapshot")
async def light_brightness() -> None:
    """Stub for test_light_brightness (port deferred)."""

@test.skip("syrupy snapshot")
async def light_rgb_color() -> None:
    """Stub for test_light_rgb_color (port deferred)."""

@test.skip("syrupy snapshot")
async def light_effect() -> None:
    """Stub for test_light_effect (port deferred)."""

@test.skip("syrupy snapshot")
async def light_invalid_effect() -> None:
    """Stub for test_light_invalid_effect (port deferred)."""

@test.skip("syrupy snapshot")
async def light_turn_on_when_on_is_noop() -> None:
    """Stub for test_light_turn_on_when_on_is_noop (port deferred)."""

@test.skip("syrupy snapshot")
async def light_state_handles_invalid_attributes_from_sse() -> None:
    """Stub for test_light_state_handles_invalid_attributes_from_sse (port deferred)."""

@test.skip("syrupy snapshot")
async def ambilight_connection_error() -> None:
    """Stub for test_ambilight_connection_error (port deferred)."""
