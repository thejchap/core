"""Tryke skip stub for test_diagnostics.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def async_get_config_entry_diagnostics() -> None:
    """Stub for test_async_get_config_entry_diagnostics."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def async_get_config_entry_diagnostics_with_battery() -> None:
    """Stub for test_async_get_config_entry_diagnostics_with_battery."""


