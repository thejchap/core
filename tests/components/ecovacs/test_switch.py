"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_entities() -> None:
    """Stub for test_switch_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def disabled_by_default_switch_entities() -> None:
    """Stub for test_disabled_by_default_switch_entities."""

