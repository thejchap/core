"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def root() -> None:
    """Stub for test_root (port deferred)."""

@test.skip("snapshot test - port deferred")
async def entry() -> None:
    """Stub for test_entry (port deferred)."""

@test.skip("snapshot test - port deferred")
async def directory() -> None:
    """Stub for test_directory (port deferred)."""

@test.skip("snapshot test - port deferred")
async def subdirectory() -> None:
    """Stub for test_subdirectory (port deferred)."""

@test.skip("snapshot test - port deferred")
async def file() -> None:
    """Stub for test_file (port deferred)."""

@test.skip("snapshot test - port deferred")
async def bad_entry() -> None:
    """Stub for test_bad_entry (port deferred)."""
