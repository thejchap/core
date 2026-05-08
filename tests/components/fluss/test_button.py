"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_press() -> None:
    """Stub for test_button_press."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def devices_without_wifi_permission_are_filtered() -> None:
    """Stub for test_devices_without_wifi_permission_are_filtered."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_unavailable_on_status_error() -> None:
    """Stub for test_button_unavailable_on_status_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_unavailable_when_internet_disconnected() -> None:
    """Stub for test_button_unavailable_when_internet_disconnected."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_press_error() -> None:
    """Stub for test_button_press_error."""

