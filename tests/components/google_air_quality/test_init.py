"""Tryke skip stub for test_init.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the google_air_quality integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.google_air_quality.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("google_air_quality")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_not_ready() -> None:
    """Stub for test_config_not_ready."""

