"""Tryke skip stub for test_alarm_control_panel.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def alarm_changed_from_external() -> None:
    """Stub for test_alarm_changed_from_external."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def alarm_changed_from_hass() -> None:
    """Stub for test_alarm_changed_from_hass."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def alarm_undefined_fetch_status() -> None:
    """Stub for test_alarm_undefined_fetch_status."""

