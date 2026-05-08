"""Tests for the Roku select platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("indirect parametrize")
async def application_state() -> None:
    """Stub for test_application_state (port deferred)."""

@test.skip("indirect parametrize")
async def application_select_error() -> None:
    """Stub for test_application_select_error (port deferred)."""

@test.skip("indirect parametrize")
async def channel_state() -> None:
    """Stub for test_channel_state (port deferred)."""

@test.skip("indirect parametrize")
async def channel_select_error() -> None:
    """Stub for test_channel_select_error (port deferred)."""
