"""Tests for the squeezebox button component. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def squeezebox_press() -> None:
    """Stub for test_squeezebox_press (port deferred)."""
