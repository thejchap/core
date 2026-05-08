"""Tryke skip-stubs for tesla_fleet/test_diagnostics.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""

