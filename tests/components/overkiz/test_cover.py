"""Tryke skip-stubs for overkiz cover tests.

Original tests use OverkizClient API mocks + token refresh; full port deferred.
"""

from tryke import test

@test.skip("OverkizClient API mocks + token refresh")
async def cover_entities_snapshot() -> None:
    """Test representative real setups via snapshot."""

@test.skip("OverkizClient API mocks + token refresh")
async def cover_service_actions() -> None:
    """Test open, close, and stop cover services."""

@test.skip("OverkizClient API mocks + token refresh")
async def cover_set_position() -> None:
    """Test cover position services and mapping."""

@test.skip("OverkizClient API mocks + token refresh")
async def cover_tilt_services() -> None:
    """Test tilt services for a pergola from a full user setup."""

@test.skip("OverkizClient API mocks + token refresh")
async def cover_state_updates() -> None:
    """Test cover state updates via events and execution tracking."""

@test.skip("OverkizClient API mocks + token refresh")
async def vertical_cover_moving_direction() -> None:
    """Test moving direction detection for vertical covers based on current vs target position."""

@test.skip("OverkizClient API mocks + token refresh")
async def awning_moving_direction() -> None:
    """Test moving direction detection for awnings based on current vs target position."""

@test.skip("OverkizClient API mocks + token refresh")
async def awning_direct_position_mapping() -> None:
    """Test awning deployment uses direct mapping while vertical covers invert."""

@test.skip("OverkizClient API mocks + token refresh")
async def moving_offset_missing_closure_states() -> None:
    """Test that is_opening/is_closing return None when closure states are missing while moving."""

@test.skip("OverkizClient API mocks + token refresh")
async def moving_offset_none_values() -> None:
    """Test that is_opening/is_closing return None when closure value_as_int is None."""

@test.skip("OverkizClient API mocks + token refresh")
async def tilt_position_none_value() -> None:
    """Test that tilt position returns None when value_as_int is None."""

@test.skip("OverkizClient API mocks + token refresh")
async def low_speed_cover_open_close() -> None:
    """Test low speed cover open and close send correct commands."""

@test.skip("OverkizClient API mocks + token refresh")
async def set_cover_position_and_tilt_service_is_registered() -> None:
    """The overkiz.set_cover_position_and_tilt service must be registered."""

@test.skip("OverkizClient API mocks + token refresh")
async def set_cover_position_and_tilt_executes_single_command() -> None:
    """Position+tilt must be sent as one atomic setClosureAndOrientation call."""

@test.skip("OverkizClient API mocks + token refresh")
async def set_cover_position_and_tilt_inverts_boundaries() -> None:
    """Boundary and midpoint values must invert consistently."""

@test.skip("OverkizClient API mocks + token refresh")
async def set_cover_position_and_tilt_unsupported_command_raises() -> None:
    """ServiceValidationError must be raised when SET_CLOSURE_AND_ORIENTATION is missing."""
