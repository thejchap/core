"""Tryke skip-stubs for test_diagnostics.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostics_config_entry() -> None:
    """Stub for test_diagnostics_config_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostics_device() -> None:
    """Stub for test_diagnostics_device."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def diagnostics_homee_device() -> None:
    """Stub for test_diagnostics_homee_device."""
