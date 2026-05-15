"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def usage_prediction_caching() -> None:
    """Stub for test_usage_prediction_caching (port deferred)."""
