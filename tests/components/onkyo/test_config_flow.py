"""Tryke skip-stubs for onkyo config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual() -> None:
    """Stub for test_manual (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_recoverable_error() -> None:
    """Stub for test_manual_recoverable_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def manual_error() -> None:
    """Stub for test_manual_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def eiscp_discovery() -> None:
    """Stub for test_eiscp_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def eiscp_discovery_error() -> None:
    """Stub for test_eiscp_discovery_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def eiscp_discovery_replace_ignored_entry() -> None:
    """Stub for test_eiscp_discovery_replace_ignored_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp_discovery() -> None:
    """Stub for test_ssdp_discovery (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def ssdp_discovery_error() -> None:
    """Stub for test_ssdp_discovery_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def configure() -> None:
    """Stub for test_configure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure() -> None:
    """Stub for test_reconfigure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_error() -> None:
    """Stub for test_reconfigure_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_flow() -> None:
    """Stub for test_options_flow (port deferred)."""
