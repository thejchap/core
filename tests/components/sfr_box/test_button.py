"""Test the SFR Box buttons. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def buttons() -> None:
    """Stub for test_buttons (port deferred)."""

@test.skip("syrupy snapshot")
async def buttons_no_auth() -> None:
    """Stub for test_buttons_no_auth (port deferred)."""

@test.skip("syrupy snapshot")
async def reboot() -> None:
    """Stub for test_reboot (port deferred)."""
