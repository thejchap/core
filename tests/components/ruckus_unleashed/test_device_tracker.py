"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def client_connected() -> None:
    """Stub for test_client_connected (port deferred)."""

@test.skip("pending tryke port")
async def client_disconnected() -> None:
    """Stub for test_client_disconnected (port deferred)."""

@test.skip("pending tryke port")
async def clients_update_failed() -> None:
    """Stub for test_clients_update_failed (port deferred)."""

@test.skip("pending tryke port")
async def clients_update_auth_failed() -> None:
    """Stub for test_clients_update_auth_failed (port deferred)."""

@test.skip("pending tryke port")
async def restoring_clients() -> None:
    """Stub for test_restoring_clients (port deferred)."""

@test.skip("pending tryke port")
async def mac_filter_tracks_only_allowed() -> None:
    """Stub for test_mac_filter_tracks_only_allowed (port deferred)."""

@test.skip("pending tryke port")
async def empty_mac_filter_tracks_all() -> None:
    """Stub for test_empty_mac_filter_tracks_all (port deferred)."""

@test.skip("pending tryke port")
async def mac_filter_restore_respects_filter() -> None:
    """Stub for test_mac_filter_restore_respects_filter (port deferred)."""
