"""Tryke skip-stubs for energyid config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_user_step_success_claimed() -> None:
    """Stub for test_config_flow_user_step_success_claimed (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_auth_and_claim_step_success() -> None:
    """Stub for test_config_flow_auth_and_claim_step_success (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_claim_timeout() -> None:
    """Stub for test_config_flow_claim_timeout (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def duplicate_unique_id_prevented() -> None:
    """Stub for test_duplicate_unique_id_prevented (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def multiple_different_devices_allowed() -> None:
    """Stub for test_multiple_different_devices_allowed (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_connection_error() -> None:
    """Stub for test_config_flow_connection_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_unexpected_error() -> None:
    """Stub for test_config_flow_unexpected_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_external_step_claimed_during_display() -> None:
    """Stub for test_config_flow_external_step_claimed_during_display (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_auth_and_claim_step_not_claimed() -> None:
    """Stub for test_config_flow_auth_and_claim_step_not_claimed (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_reauth_success() -> None:
    """Stub for test_config_flow_reauth_success (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_client_response_error() -> None:
    """Stub for test_config_flow_client_response_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def config_flow_reauth_needs_claim() -> None:
    """Stub for test_config_flow_reauth_needs_claim (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def async_get_supported_subentry_types() -> None:
    """Stub for test_async_get_supported_subentry_types (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def polling_stops_on_invalid_auth_error() -> None:
    """Stub for test_polling_stops_on_invalid_auth_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def polling_stops_on_cannot_connect_error() -> None:
    """Stub for test_polling_stops_on_cannot_connect_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def auth_and_claim_subsequent_auth_error() -> None:
    """Stub for test_auth_and_claim_subsequent_auth_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def reauth_with_error() -> None:
    """Stub for test_reauth_with_error (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def polling_cancellation_on_auth_failure() -> None:
    """Stub for test_polling_cancellation_on_auth_failure (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def polling_cancellation_on_success() -> None:
    """Stub for test_polling_cancellation_on_success (port deferred)."""
