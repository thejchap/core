"""Tryke skip stub for test_helpers.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def convert_to_waypoint_coordinates() -> None:
    """Stub for test_convert_to_waypoint_coordinates."""

