"""Tryke skip-stubs for test_backup.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def pre_backup() -> None:
    """Stub for test_pre_backup."""


@test.skip("zha: sibling test pending tryke port")
async def pre_backup_no_gateway() -> None:
    """Stub for test_pre_backup_no_gateway."""


@test.skip("zha: sibling test pending tryke port")
async def post_backup() -> None:
    """Stub for test_post_backup."""
