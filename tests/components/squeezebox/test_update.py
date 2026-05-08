"""Test squeezebox update platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_lms() -> None:
    """Stub for test_update_lms (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_plugins_install_fallback() -> None:
    """Stub for test_update_plugins_install_fallback (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_plugins_install_restart_fail() -> None:
    """Stub for test_update_plugins_install_restart_fail (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def update_plugins_install_ok() -> None:
    """Stub for test_update_plugins_install_ok (port deferred)."""
