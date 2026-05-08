"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_config_and_unload() -> None:
    """Stub for test_setup_config_and_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def legacy_setup_config_and_unload() -> None:
    """Stub for test_legacy_setup_config_and_unload."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_entry_not_ready() -> None:
    """Stub for test_async_setup_entry_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info."""

