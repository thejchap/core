"""Tryke skip stub for test_helpers.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_assistant_sdk.helpers module imports cleanly."""
    from homeassistant.components.google_assistant_sdk import helpers  # noqa: PLC0415
    expect(helpers).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_language_codes() -> None:
    """Stub for test_default_language_codes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_language_code() -> None:
    """Stub for test_default_language_code."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def best_matching_language_code() -> None:
    """Stub for test_best_matching_language_code."""

