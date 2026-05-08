"""Tryke skip stub for test_scene.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_attributes() -> None:
    """Stub for test_entity_attributes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_attributes_without_room() -> None:
    """Stub for test_entity_attributes_without_room."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def activate_scene() -> None:
    """Stub for test_activate_scene."""

