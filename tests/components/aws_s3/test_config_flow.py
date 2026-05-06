"""Tryke skip-stubs for aws_s3 config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow() -> None:
    """Stub for test_flow (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_create_client_errors() -> None:
    """Stub for test_flow_create_client_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_head_bucket_error() -> None:
    """Stub for test_flow_head_bucket_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_if_already_configured() -> None:
    """Stub for test_abort_if_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def flow_create_not_aws_endpoint() -> None:
    """Stub for test_flow_create_not_aws_endpoint (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_if_already_configured_with_same_prefix() -> None:
    """Stub for test_abort_if_already_configured_with_same_prefix (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_if_entry_without_prefix() -> None:
    """Stub for test_abort_if_entry_without_prefix (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def no_abort_if_different_prefix() -> None:
    """Stub for test_no_abort_if_different_prefix (port deferred)."""
