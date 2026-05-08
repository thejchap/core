"""Tryke skip stub for test_todo.py with one passing smoke test."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the habitica integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.habitica.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("habitica")


@test.skip("requires habiticalib mock chain + snapshot")
async def todos() -> None:
    """Stub for test_todos."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def todo_items() -> None:
    """Stub for test_todo_items."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def complete_todo_item() -> None:
    """Stub for test_complete_todo_item."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def uncomplete_todo_item() -> None:
    """Stub for test_uncomplete_todo_item."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def complete_todo_item_exception() -> None:
    """Stub for test_complete_todo_item_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_todo_item() -> None:
    """Stub for test_update_todo_item."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_todo_item_exception() -> None:
    """Stub for test_update_todo_item_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def add_todo_item() -> None:
    """Stub for test_add_todo_item."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def add_todo_item_exception() -> None:
    """Stub for test_add_todo_item_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def delete_todo_item() -> None:
    """Stub for test_delete_todo_item."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def delete_todo_item_exception() -> None:
    """Stub for test_delete_todo_item_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def delete_completed_todo_items() -> None:
    """Stub for test_delete_completed_todo_items."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def delete_completed_todo_items_exception() -> None:
    """Stub for test_delete_completed_todo_items_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def move_todo_item() -> None:
    """Stub for test_move_todo_item."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def move_todo_item_exception() -> None:
    """Stub for test_move_todo_item_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def next_due_date() -> None:
    """Stub for test_next_due_date."""

