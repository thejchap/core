"""Tryke skip stub for test_repairs.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unauthorized_triggers_reauth() -> None:
    """Stub for test_unauthorized_triggers_reauth."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def repair_issue_creation() -> None:
    """Stub for test_repair_issue_creation."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def async_create_fix_flow() -> None:
    """Stub for test_async_create_fix_flow."""

