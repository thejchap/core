"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the glances integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.glances.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("glances")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def successful_config_entry() -> None:
    """Stub for test_successful_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_error() -> None:
    """Stub for test_setup_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

