"""Tryke skip stub for test_select.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gardena_bluetooth.select module imports cleanly."""
    from homeassistant.components.gardena_bluetooth import select  # noqa: PLC0415
    expect(select).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change() -> None:
    """Stub for test_state_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select() -> None:
    """Stub for test_select."""

