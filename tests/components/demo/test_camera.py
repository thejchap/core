"""Tryke skip stub for test_camera.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def init_state_is_streaming() -> None:
    """Stub for test_init_state_is_streaming."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_on_state_back_to_streaming() -> None:
    """Stub for test_turn_on_state_back_to_streaming."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_off_image() -> None:
    """Stub for test_turn_off_image."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_off_invalid_camera() -> None:
    """Stub for test_turn_off_invalid_camera."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def motion_detection() -> None:
    """Stub for test_motion_detection."""

