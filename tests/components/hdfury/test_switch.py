"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_entities() -> None:
    """Stub for test_switch_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_turn_on_off() -> None:
    """Stub for test_switch_turn_on_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_turn_error() -> None:
    """Stub for test_switch_turn_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_entities_unavailable_on_error() -> None:
    """Stub for test_switch_entities_unavailable_on_error."""

