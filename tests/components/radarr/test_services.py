"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def get_queue_service() -> None:
    """Stub for test_get_queue_service (port deferred)."""

@test.skip("snapshot test - port deferred")
async def get_movies_service() -> None:
    """Stub for test_get_movies_service (port deferred)."""

@test.skip("snapshot test - port deferred")
async def services_api_connection_error() -> None:
    """Stub for test_services_api_connection_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def get_movies_service_api_auth_error() -> None:
    """Stub for test_get_movies_service_api_auth_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def services_invalid_entry() -> None:
    """Stub for test_services_invalid_entry (port deferred)."""

@test.skip("snapshot test - port deferred")
async def services_entry_not_loaded() -> None:
    """Stub for test_services_entry_not_loaded (port deferred)."""
