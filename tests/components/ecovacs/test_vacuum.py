"""Tryke skip stub for test_vacuum.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def clean_area() -> None:
    """Stub for test_clean_area."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def clean_area_no_map() -> None:
    """Stub for test_clean_area_no_map."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def clean_area_invalid_map_id() -> None:
    """Stub for test_clean_area_invalid_map_id."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def clean_area_room_from_not_current_map() -> None:
    """Stub for test_clean_area_room_from_not_current_map."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raise_segment_changed_issue() -> None:
    """Stub for test_raise_segment_changed_issue."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_segments() -> None:
    """Stub for test_get_segments."""

