"""Tryke skip-stubs for cookidoo config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_user_success() -> None:
    """Stub for test_flow_user_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_user_init_data_unknown_error_and_recover_on_step_1() -> None:
    """Stub for test_flow_user_init_data_unknown_error_and_recover_on_step_1 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_user_init_data_unknown_error_and_recover_on_step_2() -> None:
    """Stub for test_flow_user_init_data_unknown_error_and_recover_on_step_2 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_user_init_data_already_configured() -> None:
    """Stub for test_flow_user_init_data_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reconfigure_success() -> None:
    """Stub for test_flow_reconfigure_success (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reconfigure_init_data_unknown_error_and_recover_on_step_1() -> None:
    """Stub for test_flow_reconfigure_init_data_unknown_error_and_recover_on_step_1 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reconfigure_init_data_unknown_error_and_recover_on_step_2() -> None:
    """Stub for test_flow_reconfigure_init_data_unknown_error_and_recover_on_step_2 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reconfigure_id_mismatch() -> None:
    """Stub for test_flow_reconfigure_id_mismatch (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth() -> None:
    """Stub for test_flow_reauth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth_error_and_recover() -> None:
    """Stub for test_flow_reauth_error_and_recover (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth_id_mismatch() -> None:
    """Stub for test_flow_reauth_id_mismatch (port deferred)."""
