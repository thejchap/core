"""Tryke skip stub for test_event.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the group.event module imports cleanly."""
    from homeassistant.components.group import event  # noqa: PLC0415
    expect(event).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state."""

