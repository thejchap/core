"""Tryke skip stub for test_number.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the hdfury.number module imports cleanly."""
    from homeassistant.components.hdfury import number  # noqa: PLC0415
    expect(number).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_entities() -> None:
    """Stub for test_number_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_set_value() -> None:
    """Stub for test_number_set_value."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_error() -> None:
    """Stub for test_number_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_entities_unavailable_on_error() -> None:
    """Stub for test_number_entities_unavailable_on_error."""

