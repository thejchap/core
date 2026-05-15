"""Tryke skip stub (requires unported fixture)."""

from tryke import test


@test.skip("requires recorder_mock (not in tryke shim)")
async def common_control() -> None:
    """Stub for test_common_control (port deferred)."""

@test.skip("requires recorder_mock (not in tryke shim)")
async def caching_behavior() -> None:
    """Stub for test_caching_behavior (port deferred)."""
