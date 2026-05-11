"""Tryke skip stub for test_cover.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("snapshot test — out of scope")
async def cover_open() -> None:
    """Stub for test_cover_open."""


@test.skip("snapshot test — out of scope")
async def cover_close() -> None:
    """Stub for test_cover_close."""


@test.skip("snapshot test — out of scope")
async def cover_stop_if_stopped() -> None:
    """Stub for test_cover_stop_if_stopped."""


@test.skip("snapshot test — out of scope")
async def cover_restore_state() -> None:
    """Stub for test_cover_restore_state."""


@test.skip("snapshot test — out of scope")
async def cover_dynamic() -> None:
    """Stub for test_cover_dynamic."""


