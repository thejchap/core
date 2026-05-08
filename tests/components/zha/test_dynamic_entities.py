"""Tryke skip-stubs for test_dynamic_entities.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def dynamic_entity_lifecycle() -> None:
    """Stub for test_dynamic_entity_lifecycle."""


@test.skip("zha: sibling test pending tryke port")
async def unknown_unique_id_is_noop() -> None:
    """Stub for test_unknown_unique_id_is_noop."""


@test.skip("zha: sibling test pending tryke port")
async def remove_entity_reference_when_ieee_already_cleared() -> None:
    """Stub for test_remove_entity_reference_when_ieee_already_cleared."""
