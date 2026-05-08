"""Tryke skip-stubs for test_todo.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def add_item() -> None:
    """Stub for test_add_item."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def remove_item() -> None:
    """Stub for test_remove_item."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def bulk_remove() -> None:
    """Stub for test_bulk_remove."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def update_item() -> None:
    """Stub for test_update_item."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def update_existing_field() -> None:
    """Stub for test_update_existing_field."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def rename() -> None:
    """Stub for test_rename."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def move_item() -> None:
    """Stub for test_move_item."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def move_item_unknown() -> None:
    """Stub for test_move_item_unknown."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def move_item_previous_unknown() -> None:
    """Stub for test_move_item_previous_unknown."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def parse_existing_ics() -> None:
    """Stub for test_parse_existing_ics."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def susbcribe() -> None:
    """Stub for test_susbcribe."""
