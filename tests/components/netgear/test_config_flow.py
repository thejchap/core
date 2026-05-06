"""Tryke skip-stubs for netgear config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user() -> None:
    """Stub for test_user (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_connect_error() -> None:
    """Stub for test_user_connect_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_incomplete_info() -> None:
    """Stub for test_user_incomplete_info (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def abort_if_already_setup() -> None:
    """Stub for test_abort_if_already_setup (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp_already_configured() -> None:
    """Stub for test_ssdp_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp_no_serial() -> None:
    """Stub for test_ssdp_no_serial (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp_ipv6() -> None:
    """Stub for test_ssdp_ipv6 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp() -> None:
    """Stub for test_ssdp (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp_port_5555() -> None:
    """Stub for test_ssdp_port_5555 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
