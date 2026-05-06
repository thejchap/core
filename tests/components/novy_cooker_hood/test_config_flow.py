"""Tryke skip-stubs for novy_cooker_hood config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_test_then_finish() -> None:
    """Stub for test_user_flow_test_then_finish (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_retry_picks_different_code() -> None:
    """Stub for test_user_flow_retry_picks_different_code (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_flow_test_transmit_failure() -> None:
    """Stub for test_user_flow_test_transmit_failure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def unique_id_already_configured() -> None:
    """Stub for test_unique_id_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def same_transmitter_different_code_is_allowed() -> None:
    """Stub for test_same_transmitter_different_code_is_allowed (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def no_transmitters() -> None:
    """Stub for test_no_transmitters (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def no_compatible_transmitters() -> None:
    """Stub for test_no_compatible_transmitters (port deferred)."""
