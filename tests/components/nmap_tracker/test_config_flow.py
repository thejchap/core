"""Tryke skip-stubs for nmap_tracker config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_range() -> None:
    """Stub for test_form_range (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_invalid_hosts() -> None:
    """Stub for test_form_invalid_hosts (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_invalid_ip_excludes() -> None:
    """Stub for test_form_invalid_ip_excludes (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_invalid_mac_excludes() -> None:
    """Stub for test_form_invalid_mac_excludes (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
