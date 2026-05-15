"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def select() -> None:
    """Stub for test_select (port deferred)."""

@test.skip("snapshot test - port deferred")
async def no_select() -> None:
    """Stub for test_no_select (port deferred)."""

@test.skip("snapshot test - port deferred")
async def select_relay_actions() -> None:
    """Stub for test_select_relay_actions (port deferred)."""

@test.skip("snapshot test - port deferred")
async def select_relay_modes() -> None:
    """Stub for test_select_relay_modes (port deferred)."""

@test.skip("snapshot test - port deferred")
async def update_dry_contact_actions_with_error() -> None:
    """Stub for test_update_dry_contact_actions_with_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def select_storage_modes() -> None:
    """Stub for test_select_storage_modes (port deferred)."""

@test.skip("snapshot test - port deferred")
async def set_storage_modes_with_error() -> None:
    """Stub for test_set_storage_modes_with_error (port deferred)."""

@test.skip("snapshot test - port deferred")
async def select_storage_modes_if_none() -> None:
    """Stub for test_select_storage_modes_if_none (port deferred)."""
