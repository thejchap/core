"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the geocaching integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.geocaching.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("geocaching")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available (port deferred)."""


