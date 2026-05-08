"""Tryke skip stubs for test_init - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_error() -> None:
    """Stub for test_setup_entry_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_success() -> None:
    """Stub for test_setup_entry_success (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_builds_ssl_context_in_executor() -> None:
    """Stub for test_setup_entry_builds_ssl_context_in_executor (port deferred)."""


