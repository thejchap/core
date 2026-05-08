"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config() -> None:
    """Stub for test_config."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def bluetooth_error_unavailable() -> None:
    """Stub for test_bluetooth_error_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def connected_state() -> None:
    """Stub for test_connected_state."""

