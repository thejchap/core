"""Tryke skip-stubs for test_remote.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xbox: sibling test pending tryke port")
async def remotes() -> None:
    """Stub for test_remotes."""


@test.skip("xbox: sibling test pending tryke port")
async def send_button_command() -> None:
    """Stub for test_send_button_command."""


@test.skip("xbox: sibling test pending tryke port")
async def send_command() -> None:
    """Stub for test_send_command."""


@test.skip("xbox: sibling test pending tryke port")
async def send_text() -> None:
    """Stub for test_send_text."""


@test.skip("xbox: sibling test pending tryke port")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("xbox: sibling test pending tryke port")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("xbox: sibling test pending tryke port")
async def send_command_exceptions() -> None:
    """Stub for test_send_command_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def turn_on_exceptions() -> None:
    """Stub for test_turn_on_exceptions."""


@test.skip("xbox: sibling test pending tryke port")
async def turn_off_exceptions() -> None:
    """Stub for test_turn_off_exceptions."""
