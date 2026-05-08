"""Tests for the Sonarr sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def disabled_by_default_sensors() -> None:
    """Stub for test_disabled_by_default_sensors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def availability() -> None:
    """Stub for test_availability (port deferred)."""
