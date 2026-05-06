"""Tryke skip-stubs for playstation_network config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_config() -> None:
    """Stub for test_manual_config (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_already_configured_as_subentry() -> None:
    """Stub for test_form_already_configured_as_subentry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_failures() -> None:
    """Stub for test_form_failures (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def parse_npsso_token_failures() -> None:
    """Stub for test_parse_npsso_token_failures (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth() -> None:
    """Stub for test_flow_reauth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth_errors() -> None:
    """Stub for test_flow_reauth_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth_token_error() -> None:
    """Stub for test_flow_reauth_token_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reauth_account_mismatch() -> None:
    """Stub for test_flow_reauth_account_mismatch (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_reconfigure() -> None:
    """Stub for test_flow_reconfigure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def add_friend_flow() -> None:
    """Stub for test_add_friend_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def add_friend_flow_already_configured() -> None:
    """Stub for test_add_friend_flow_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def add_friend_flow_already_configured_as_entry() -> None:
    """Stub for test_add_friend_flow_already_configured_as_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def add_friend_flow_no_friends() -> None:
    """Stub for test_add_friend_flow_no_friends (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def add_friend_disabled_config_entry() -> None:
    """Stub for test_add_friend_disabled_config_entry (port deferred)."""
