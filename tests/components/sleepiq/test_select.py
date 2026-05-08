"""Tests for the SleepIQ select platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def split_foundation_preset() -> None:
    """Stub for test_split_foundation_preset (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def single_foundation_preset() -> None:
    """Stub for test_single_foundation_preset (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def foot_warmer() -> None:
    """Stub for test_foot_warmer (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def core_climate() -> None:
    """Stub for test_core_climate (port deferred)."""
