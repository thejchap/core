"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the gree integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.gree.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("gree")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_simple() -> None:
    """Stub for test_setup_simple."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""

