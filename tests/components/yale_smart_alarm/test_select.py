"""Tryke skip-stubs for test_select.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def select() -> None:
    """Stub for test_switch (named test_switch in select.py upstream)."""
