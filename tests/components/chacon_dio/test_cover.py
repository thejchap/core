"""Tryke skip stub for test_cover.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update() -> None:
    """Stub for test_update."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def cover_actions() -> None:
    """Stub for test_cover_actions."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def cover_callbacks() -> None:
    """Stub for test_cover_callbacks."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def no_cover_found() -> None:
    """Stub for test_no_cover_found."""


