"""Test the Sleep as Android event platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("syrupy snapshot")
async def webhook_event() -> None:
    """Stub for test_webhook_event (port deferred)."""

@test.skip("syrupy snapshot")
async def webhook_invalid() -> None:
    """Stub for test_webhook_invalid (port deferred)."""
