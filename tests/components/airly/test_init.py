"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_not_ready() -> None:
    """Stub for test_config_not_ready."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_without_unique_id() -> None:
    """Stub for test_config_without_unique_id."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def config_with_turned_off_station() -> None:
    """Stub for test_config_with_turned_off_station."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_interval() -> None:
    """Stub for test_update_interval."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def migrate_device_entry() -> None:
    """Stub for test_migrate_device_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_air_quality_entities() -> None:
    """Stub for test_remove_air_quality_entities."""

