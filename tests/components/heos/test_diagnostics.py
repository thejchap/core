"""Tryke skip stub for test_diagnostics.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_diagnostics() -> None:
    """Stub for test_config_entry_diagnostics."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def config_entry_diagnostics_error_getting_system() -> None:
    """Stub for test_config_entry_diagnostics_error_getting_system."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_diagnostics() -> None:
    """Stub for test_device_diagnostics."""

