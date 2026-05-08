"""Tryke skip stub for test_number.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gardena_bluetooth.number module imports cleanly."""
    from homeassistant.components.gardena_bluetooth import number  # noqa: PLC0415
    expect(number).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config() -> None:
    """Stub for test_config."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def bluetooth_error_unavailable() -> None:
    """Stub for test_bluetooth_error_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def connected_state() -> None:
    """Stub for test_connected_state."""

