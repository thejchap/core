"""Tryke skip stubs for test_init - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def removing_old_device() -> None:
    """Stub for test_removing_old_device (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_invalid_registry_entry() -> None:
    """Stub for test_load_invalid_registry_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_missing_device_tracker() -> None:
    """Stub for test_load_missing_device_tracker (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_missing_required_attribute() -> None:
    """Stub for test_load_missing_required_attribute (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_valid_device_tracker() -> None:
    """Stub for test_load_valid_device_tracker (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def filter_expired_warnings() -> None:
    """Stub for test_filter_expired_warnings (port deferred)."""


