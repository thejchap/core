"""Tests for the Rituals Perfume Genie sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensors_diffuser_v1_battery_cartridge() -> None:
    """Stub for test_sensors_diffuser_v1_battery_cartridge (port deferred)."""
