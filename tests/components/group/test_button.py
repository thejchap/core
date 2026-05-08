"""Tryke skip stub for test_button.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the group.button module imports cleanly."""
    from homeassistant.components.group import button  # noqa: PLC0415
    expect(button).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting() -> None:
    """Stub for test_state_reporting."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_calls() -> None:
    """Stub for test_service_calls."""

