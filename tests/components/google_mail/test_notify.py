"""Tryke skip stub for test_notify.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_mail.notify module imports cleanly."""
    from homeassistant.components.google_mail import notify  # noqa: PLC0415
    expect(notify).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify() -> None:
    """Stub for test_notify."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_voluptuous_error() -> None:
    """Stub for test_notify_voluptuous_error."""

