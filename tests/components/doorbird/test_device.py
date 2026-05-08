"""Tryke skip stub for test_device.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def stale_favorites_filtered_by_url() -> None:
    """Stub for test_stale_favorites_filtered_by_url."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def custom_url_used_for_favorites() -> None:
    """Stub for test_custom_url_used_for_favorites."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def no_configured_events() -> None:
    """Stub for test_no_configured_events."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def change_schedule_success() -> None:
    """Stub for test_change_schedule_success."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def change_schedule_fails() -> None:
    """Stub for test_change_schedule_fails."""

