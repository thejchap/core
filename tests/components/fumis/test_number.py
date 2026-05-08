"""Tryke skip stub for test_number.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fumis.number module imports cleanly."""
    from homeassistant.components.fumis import number  # noqa: PLC0415
    expect(number).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def numbers() -> None:
    """Stub for test_numbers."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_power_level() -> None:
    """Stub for test_set_power_level."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_fan_speed() -> None:
    """Stub for test_set_fan_speed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def number_error_handling() -> None:
    """Stub for test_number_error_handling."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def numbers_disabled_by_default() -> None:
    """Stub for test_numbers_disabled_by_default."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def numbers_conditional_creation() -> None:
    """Stub for test_numbers_conditional_creation."""

