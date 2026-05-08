"""Tryke skip stub for test_binary_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fyta.binary_sensor module imports cleanly."""
    from homeassistant.components.fyta import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_entities() -> None:
    """Stub for test_all_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def connection_error() -> None:
    """Stub for test_connection_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def add_remove_entities() -> None:
    """Stub for test_add_remove_entities."""

