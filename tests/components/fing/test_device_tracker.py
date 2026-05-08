"""Tryke skip stub for test_device_tracker.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def new_device_found() -> None:
    """Stub for test_new_device_found."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_modified() -> None:
    """Stub for test_device_modified."""

