"""Tryke skip-stubs for test_device_action.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def get_actions() -> None:
    """Stub for test_get_actions."""


@test.skip("zha: sibling test pending tryke port")
async def action() -> None:
    """Stub for test_action."""


@test.skip("zha: sibling test pending tryke port")
async def invalid_zha_event_type() -> None:
    """Stub for test_invalid_zha_event_type."""


@test.skip("zha: sibling test pending tryke port")
async def client_unique_id_suffix_stripped() -> None:
    """Stub for test_client_unique_id_suffix_stripped."""
