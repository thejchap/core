"""Tryke skip stub for test_climate.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the geniushub.climate module imports cleanly."""
    from homeassistant.components.geniushub import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def cloud_all_sensors() -> None:
    """Stub for test_cloud_all_sensors."""

