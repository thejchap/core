"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the gios integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.gios.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("gios")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_not_ready() -> None:
    """Stub for test_config_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_device_and_config_entry() -> None:
    """Stub for test_migrate_device_and_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_unique_id_to_str() -> None:
    """Stub for test_migrate_unique_id_to_str."""

