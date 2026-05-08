"""Test the Saunum climate platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def climate_service_calls() -> None:
    """Stub for test_climate_service_calls (port deferred)."""

@test.skip("syrupy snapshot")
async def hvac_mode_door_open_validation() -> None:
    """Stub for test_hvac_mode_door_open_validation (port deferred)."""

@test.skip("syrupy snapshot")
async def hvac_actions() -> None:
    """Stub for test_hvac_actions (port deferred)."""

@test.skip("syrupy snapshot")
async def temperature_attributes() -> None:
    """Stub for test_temperature_attributes (port deferred)."""

@test.skip("syrupy snapshot")
async def entity_unavailable_on_update_failure() -> None:
    """Stub for test_entity_unavailable_on_update_failure (port deferred)."""

@test.skip("syrupy snapshot")
async def service_error_handling() -> None:
    """Stub for test_service_error_handling (port deferred)."""

@test.skip("syrupy snapshot")
async def fan_mode_service_call() -> None:
    """Stub for test_fan_mode_service_call (port deferred)."""

@test.skip("syrupy snapshot")
async def preset_mode_service_call() -> None:
    """Stub for test_preset_mode_service_call (port deferred)."""

@test.skip("syrupy snapshot")
async def fan_mode_attributes() -> None:
    """Stub for test_fan_mode_attributes (port deferred)."""

@test.skip("syrupy snapshot")
async def fan_mode_validation_error() -> None:
    """Stub for test_fan_mode_validation_error (port deferred)."""

@test.skip("syrupy snapshot")
async def preset_mode_validation_error() -> None:
    """Stub for test_preset_mode_validation_error (port deferred)."""

@test.skip("syrupy snapshot")
async def preset_mode_attributes_default_names() -> None:
    """Stub for test_preset_mode_attributes_default_names (port deferred)."""

@test.skip("syrupy snapshot")
async def preset_mode_attributes_custom_names() -> None:
    """Stub for test_preset_mode_attributes_custom_names (port deferred)."""

@test.skip("syrupy snapshot")
async def preset_mode_options_update() -> None:
    """Stub for test_preset_mode_options_update (port deferred)."""

@test.skip("syrupy snapshot")
async def fan_mode_error_handling() -> None:
    """Stub for test_fan_mode_error_handling (port deferred)."""
