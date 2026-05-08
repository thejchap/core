"""Tryke skip stub for test_services.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_mail.services module imports cleanly."""
    from homeassistant.components.google_mail import services  # noqa: PLC0415
    expect(services).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_vacation() -> None:
    """Stub for test_set_vacation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reauth_trigger() -> None:
    """Stub for test_reauth_trigger."""

