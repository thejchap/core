"""Tryke skip-stubs for test_device_action.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_actions() -> None:
    """Stub for test_get_actions."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_actions_meter() -> None:
    """Stub for test_get_actions_meter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def actions() -> None:
    """Stub for test_actions."""


@test.skip("zwave_js: sibling test pending tryke port")
async def actions_legacy() -> None:
    """Stub for test_actions_legacy."""


@test.skip("zwave_js: sibling test pending tryke port")
async def actions_multiple_calls() -> None:
    """Stub for test_actions_multiple_calls."""


@test.skip("zwave_js: sibling test pending tryke port")
async def lock_actions() -> None:
    """Stub for test_lock_actions."""


@test.skip("zwave_js: sibling test pending tryke port")
async def reset_meter_action() -> None:
    """Stub for test_reset_meter_action."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_action_capabilities() -> None:
    """Stub for test_get_action_capabilities."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_action_capabilities_lock_triggers() -> None:
    """Stub for test_get_action_capabilities_lock_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_action_capabilities_meter_triggers() -> None:
    """Stub for test_get_action_capabilities_meter_triggers."""


@test.skip("zwave_js: sibling test pending tryke port")
async def failure_scenarios() -> None:
    """Stub for test_failure_scenarios."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unavailable_entity_actions() -> None:
    """Stub for test_unavailable_entity_actions."""


@test.skip("zwave_js: sibling test pending tryke port")
async def action_schema_coerces_string_command_class() -> None:
    """Stub for test_action_schema_coerces_string_command_class."""
