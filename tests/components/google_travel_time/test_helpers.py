"""Tryke skip stub for test_helpers.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_travel_time.helpers module imports cleanly."""
    from homeassistant.components.google_travel_time import helpers  # noqa: PLC0415
    expect(helpers).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def convert_to_waypoint_coordinates() -> None:
    """Stub for test_convert_to_waypoint_coordinates."""

