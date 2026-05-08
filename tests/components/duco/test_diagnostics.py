"""Tryke skip stubs for test_diagnostics - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostics() -> None:
    """Stub for test_diagnostics (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostics_connection_error() -> None:
    """Stub for test_diagnostics_connection_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostics_without_optional_board_metadata() -> None:
    """Stub for test_diagnostics_without_optional_board_metadata (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def diagnostics_without_optional_api_metadata() -> None:
    """Stub for test_diagnostics_without_optional_api_metadata (port deferred)."""


