"""Tryke skip stub for test_services.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_reaction() -> None:
    """Stub for test_send_reaction."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_reaction_exception() -> None:
    """Stub for test_send_reaction_exception."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_reaction_config_entry_not_loaded() -> None:
    """Stub for test_send_reaction_config_entry_not_loaded."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_reaction_unknown_entity() -> None:
    """Stub for test_send_reaction_unknown_entity."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def send_reaction_not_found() -> None:
    """Stub for test_send_reaction_not_found."""

