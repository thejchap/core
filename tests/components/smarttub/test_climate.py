"""Test the SmartTub climate platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def thermostat_state() -> None:
    """Stub for test_thermostat_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def thermostat_hvac_action_update() -> None:
    """Stub for test_thermostat_hvac_action_update (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def thermostat_set_temperature() -> None:
    """Stub for test_thermostat_set_temperature (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def thermostat_set_preset_mode() -> None:
    """Stub for test_thermostat_set_preset_mode (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def thermostat_api_error() -> None:
    """Stub for test_thermostat_api_error (port deferred)."""
