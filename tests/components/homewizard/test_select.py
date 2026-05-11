"""Tryke skip-stubs for test_select.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.homewizard.select module imports cleanly."""
    from homeassistant.components.homewizard import select  # noqa: PLC0415
    expect(select).not_.to_be(None)


@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def entities_not_created_for_device() -> None:
    """Stub for test_entities_not_created_for_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def select_entity_snapshots() -> None:
    """Stub for test_select_entity_snapshots."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def select_set_option() -> None:
    """Stub for test_select_set_option."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def select_request_error() -> None:
    """Stub for test_select_request_error."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def select_unauthorized_error() -> None:
    """Stub for test_select_unauthorized_error."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def select_unreachable() -> None:
    """Stub for test_select_unreachable."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def select_multiple_state_changes() -> None:
    """Stub for test_select_multiple_state_changes."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def disabled_by_default_selects() -> None:
    """Stub for test_disabled_by_default_selects."""
