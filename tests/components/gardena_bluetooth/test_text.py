"""Tryke skip stub for test_text.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gardena_bluetooth.text module imports cleanly."""
    from homeassistant.components.gardena_bluetooth import text  # noqa: PLC0415
    expect(text).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def text_set_value() -> None:
    """Stub for test_text_set_value."""

