"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the gentex_homelink integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.gentex_homelink.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("gentex_homelink")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device() -> None:
    """Stub for test_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_sync() -> None:
    """Stub for test_reload_sync."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available."""

