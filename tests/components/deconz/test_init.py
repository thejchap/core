"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def get_deconz_api_fails() -> None:
    """Stub for test_get_deconz_api_fails (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_fails_trigger_reauth_flow() -> None:
    """Stub for test_setup_entry_fails_trigger_reauth_flow (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_multiple_gateways() -> None:
    """Stub for test_setup_entry_multiple_gateways (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry_multiple_gateways() -> None:
    """Stub for test_unload_entry_multiple_gateways (port deferred)."""

@test.skip("pending tryke port")
async def unload_entry_multiple_gateways_parallel() -> None:
    """Stub for test_unload_entry_multiple_gateways_parallel (port deferred)."""
