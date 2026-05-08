"""Test the SmartTub sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def null_blowoutcycle() -> None:
    """Stub for test_null_blowoutcycle (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def primary_filtration() -> None:
    """Stub for test_primary_filtration (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def secondary_filtration() -> None:
    """Stub for test_secondary_filtration (port deferred)."""
