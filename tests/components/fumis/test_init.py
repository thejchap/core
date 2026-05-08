"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the fumis integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.fumis.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("fumis")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_authentication_failed() -> None:
    """Stub for test_config_entry_authentication_failed."""

