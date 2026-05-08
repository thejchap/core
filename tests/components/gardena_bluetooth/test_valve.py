"""Tryke skip stub for test_valve.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gardena_bluetooth.valve module imports cleanly."""
    from homeassistant.components.gardena_bluetooth import valve  # noqa: PLC0415
    expect(valve).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switching() -> None:
    """Stub for test_switching."""

