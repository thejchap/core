"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the harmony integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.harmony.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("harmony")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unique_id_migration() -> None:
    """Stub for test_unique_id_migration."""

