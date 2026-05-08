"""Tryke skip stub for test_diagnostics.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def get_config_entry_diagnostics() -> None:
    """Stub for test_get_config_entry_diagnostics."""

