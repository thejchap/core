"""Tests for the SMLIGHT switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def switch_setup() -> None:
    """Stub for test_switch_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def disabled_by_default_switch() -> None:
    """Stub for test_disabled_by_default_switch (port deferred)."""

@test.skip("syrupy snapshot")
async def switches() -> None:
    """Stub for test_switches (port deferred)."""
