"""Tryke skip stubs for test_init - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_success() -> None:
    """Stub for test_setup_entry_success (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_entry_oserror_raises_not_ready() -> None:
    """Stub for test_setup_entry_oserror_raises_not_ready (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_registry_not_updated_on_identical_callback() -> None:
    """Stub for test_device_registry_not_updated_on_identical_callback (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_registry_updated_on_sw_version_change() -> None:
    """Stub for test_device_registry_updated_on_sw_version_change (port deferred)."""


