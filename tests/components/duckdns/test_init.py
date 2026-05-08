"""Tryke skip stubs for test_init - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_backoff() -> None:
    """Stub for test_setup_backoff (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_set_txt() -> None:
    """Stub for test_service_set_txt (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_clear_txt() -> None:
    """Stub for test_service_clear_txt (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_exceptions() -> None:
    """Stub for test_service_exceptions (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_request_exception() -> None:
    """Stub for test_service_request_exception (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_select_entry() -> None:
    """Stub for test_service_select_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload (port deferred)."""


