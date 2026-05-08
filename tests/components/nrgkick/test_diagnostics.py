"""Tryke skip-stub for nrgkick/test_diagnostics (snapshot-based)."""

from tryke import test


@test.skip("requires syrupy snapshot fixture (not in tryke shim)")
async def diagnostics() -> None:
    """Stub for test_diagnostics (port deferred)."""
