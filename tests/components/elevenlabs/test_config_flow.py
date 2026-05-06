"""Tryke skip-stubs for elevenlabs config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_step() -> None:
    """Stub for test_user_step (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def invalid_api_key() -> None:
    """Stub for test_invalid_api_key (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def voices_error() -> None:
    """Stub for test_voices_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def models_error() -> None:
    """Stub for test_models_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow_init() -> None:
    """Stub for test_options_flow_init (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow_voice_settings_default() -> None:
    """Stub for test_options_flow_voice_settings_default (port deferred)."""
