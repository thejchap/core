"""Tests for the Sonos number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def number_entities() -> None:
    """Stub for test_number_entities (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def amp_number_entities() -> None:
    """Stub for test_amp_number_entities (port deferred)."""
