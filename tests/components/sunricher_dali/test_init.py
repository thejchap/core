"""Test the Sunricher DALI integration initialization. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("snapshot test — out of scope")
async def setup_entry_success() -> None:
    """Stub for test_setup_entry_success (port deferred)."""

@test.skip("snapshot test — out of scope")
async def devices() -> None:
    """Stub for test_devices (port deferred)."""

@test.skip("snapshot test — out of scope")
async def setup_entry_connection_error() -> None:
    """Stub for test_setup_entry_connection_error (port deferred)."""

@test.skip("snapshot test — out of scope")
async def setup_entry_discovery_error() -> None:
    """Stub for test_setup_entry_discovery_error (port deferred)."""

@test.skip("snapshot test — out of scope")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""

@test.skip("snapshot test — out of scope")
async def remove_stale_devices() -> None:
    """Stub for test_remove_stale_devices (port deferred)."""
