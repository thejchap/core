"""Tryke skip-stubs for teslemetry/test_diagnostics.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def diagnostics() -> None:
    """Stub for test_diagnostics."""

