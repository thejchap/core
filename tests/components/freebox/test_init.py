"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the freebox integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.freebox.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("freebox")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_import() -> None:
    """Stub for test_setup_import."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_remove() -> None:
    """Stub for test_unload_remove."""

