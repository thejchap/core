"""Tryke skip stub for test_todo.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.caldav.todo module imports cleanly."""
    from homeassistant.components.caldav import todo  # noqa: PLC0415
    expect(todo).not_.to_be(None)


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def todo_list_state() -> None:
    """Stub for test_todo_list_state."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def supported_components() -> None:
    """Stub for test_supported_components."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def add_item() -> None:
    """Stub for test_add_item."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def add_item_failure() -> None:
    """Stub for test_add_item_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_item() -> None:
    """Stub for test_update_item."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_item_failure() -> None:
    """Stub for test_update_item_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def update_item_lookup_failure() -> None:
    """Stub for test_update_item_lookup_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_item() -> None:
    """Stub for test_remove_item."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_item_lookup_failure() -> None:
    """Stub for test_remove_item_lookup_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_item_failure() -> None:
    """Stub for test_remove_item_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remove_item_not_found() -> None:
    """Stub for test_remove_item_not_found."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def subscribe() -> None:
    """Stub for test_subscribe."""

