"""Tryke skip-stubs for test_number.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def number() -> None:
    """Stub for test_number."""


@test.skip("zha: sibling test pending tryke port")
async def number_quirks_v2_metadata() -> None:
    """Stub for test_number_quirks_v2_metadata."""
