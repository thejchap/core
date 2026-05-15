"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def minio_services() -> None:
    """Stub for test_minio_services (port deferred)."""

@test.skip("pending tryke port")
async def minio_listen() -> None:
    """Stub for test_minio_listen (port deferred)."""

@test.skip("pending tryke port")
async def queue_listener() -> None:
    """Stub for test_queue_listener (port deferred)."""
