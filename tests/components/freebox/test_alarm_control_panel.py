"""Tryke skip stub for test_alarm_control_panel.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the freebox.alarm_control_panel module imports cleanly."""
    from homeassistant.components.freebox import alarm_control_panel  # noqa: PLC0415
    expect(alarm_control_panel).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def alarm_changed_from_external() -> None:
    """Stub for test_alarm_changed_from_external."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def alarm_changed_from_hass() -> None:
    """Stub for test_alarm_changed_from_hass."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def alarm_undefined_fetch_status() -> None:
    """Stub for test_alarm_undefined_fetch_status."""

