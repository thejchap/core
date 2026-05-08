"""Test the snapcast media player implementation. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def state() -> None:
    """Stub for test_state (port deferred)."""

@test.skip("syrupy snapshot")
async def join() -> None:
    """Stub for test_join (port deferred)."""

@test.skip("syrupy snapshot")
async def unjoin() -> None:
    """Stub for test_unjoin (port deferred)."""

@test.skip("syrupy snapshot")
async def join_non_snapcast_client() -> None:
    """Stub for test_join_non_snapcast_client (port deferred)."""

@test.skip("syrupy snapshot")
async def join_different_server() -> None:
    """Stub for test_join_different_server (port deferred)."""

@test.skip("syrupy snapshot")
async def join_client_key_error() -> None:
    """Stub for test_join_client_key_error (port deferred)."""

@test.skip("syrupy snapshot")
async def join_client_identifier_underscore() -> None:
    """Stub for test_join_client_identifier_underscore (port deferred)."""

@test.skip("syrupy snapshot")
async def stream_not_found() -> None:
    """Stub for test_stream_not_found (port deferred)."""

@test.skip("syrupy snapshot")
async def state_stream_not_found() -> None:
    """Stub for test_state_stream_not_found (port deferred)."""

@test.skip("syrupy snapshot")
async def attributes_group_is_none() -> None:
    """Stub for test_attributes_group_is_none (port deferred)."""

@test.skip("syrupy snapshot")
async def select_source_group_is_none() -> None:
    """Stub for test_select_source_group_is_none (port deferred)."""

@test.skip("syrupy snapshot")
async def join_group_is_none() -> None:
    """Stub for test_join_group_is_none (port deferred)."""

@test.skip("syrupy snapshot")
async def unjoin_group_is_none() -> None:
    """Stub for test_unjoin_group_is_none (port deferred)."""
