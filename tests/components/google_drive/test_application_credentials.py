"""Tryke skip stub for test_application_credentials.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_drive.application_credentials module imports cleanly."""
    from homeassistant.components.google_drive import application_credentials  # noqa: PLC0415
    expect(application_credentials).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def description_placeholders() -> None:
    """Stub for test_description_placeholders."""

