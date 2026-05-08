"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_setup() -> None:
    """Stub for test_config_entry_setup."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready_get_devices_error() -> None:
    """Stub for test_config_entry_not_ready_get_devices_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_entry_not_ready_get_energy_use_data_error() -> None:
    """Stub for test_config_entry_not_ready_get_energy_use_data_error."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""

