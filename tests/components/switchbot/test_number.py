"""Tests for the switchbot number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def meter_pro_co2_display_time_offset_initial_state() -> None:
    """Stub for test_meter_pro_co2_display_time_offset_initial_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def meter_pro_co2_set_display_time_offset() -> None:
    """Stub for test_meter_pro_co2_set_display_time_offset (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_display_time_offset_out_of_range() -> None:
    """Stub for test_set_display_time_offset_out_of_range (port deferred)."""
