"""Tryke skip stub for test_todo.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.cookidoo.todo module imports cleanly."""
    from homeassistant.components.cookidoo import todo  # noqa: PLC0415
    expect(todo).not_.to_be(None)


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def todo() -> None:
    """Stub for test_todo."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_ingredient() -> None:
    """Stub for test_update_ingredient."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_ingredient_exception() -> None:
    """Stub for test_update_ingredient_exception."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def add_additional_item() -> None:
    """Stub for test_add_additional_item."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def add_additional_item_exception() -> None:
    """Stub for test_add_additional_item_exception."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_additional_item() -> None:
    """Stub for test_update_additional_item."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def update_additional_item_exception() -> None:
    """Stub for test_update_additional_item_exception."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def delete_additional_items() -> None:
    """Stub for test_delete_additional_items."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def delete_additional_items_exception() -> None:
    """Stub for test_delete_additional_items_exception."""


