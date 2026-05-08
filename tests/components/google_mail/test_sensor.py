"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_mail.sensor module imports cleanly."""
    from homeassistant.components.google_mail import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_reauth_trigger() -> None:
    """Stub for test_sensor_reauth_trigger."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_token_error_no_reauth() -> None:
    """Stub for test_sensor_token_error_no_reauth."""

