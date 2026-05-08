"""Tryke skip stub for test_diagnostics.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""


@test.skip("uses syrupy snapshot — needs pytest --snapshot-update first")
async def diagnostics_without_static_values() -> None:
    """Stub for test_diagnostics_without_static_values."""


