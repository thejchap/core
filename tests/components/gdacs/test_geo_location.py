"""Tryke skip stub for test_geo_location.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gdacs.geo_location module imports cleanly."""
    from homeassistant.components.gdacs import geo_location  # noqa: PLC0415
    expect(geo_location).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_imperial() -> None:
    """Stub for test_setup_imperial."""

