"""Test sky_remote remote. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_command() -> None:
    """Stub for test_send_command (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_invalid_command() -> None:
    """Stub for test_send_invalid_command (port deferred)."""
