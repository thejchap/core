"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the goodwe integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.goodwe.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("goodwe")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migration() -> None:
    """Stub for test_migration."""

