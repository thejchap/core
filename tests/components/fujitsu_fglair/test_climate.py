"""Tryke skip stub for test_climate.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fujitsu_fglair.climate module imports cleanly."""
    from homeassistant.components.fujitsu_fglair import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_attributes() -> None:
    """Stub for test_set_attributes."""

