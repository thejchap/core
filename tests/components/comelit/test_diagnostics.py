"""Tryke skip stub for test_diagnostics.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entry_diagnostics_bridge() -> None:
    """Stub for test_entry_diagnostics_bridge."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def entry_diagnostics_vedo() -> None:
    """Stub for test_entry_diagnostics_vedo."""


