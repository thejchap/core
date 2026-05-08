"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the generic integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.generic.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("generic")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_on_title_change() -> None:
    """Stub for test_reload_on_title_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration_to_version_2() -> None:
    """Stub for test_migration_to_version_2."""

