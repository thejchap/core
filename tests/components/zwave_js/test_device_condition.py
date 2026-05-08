"""Tryke skip-stubs for test_device_condition.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_conditions() -> None:
    """Stub for test_get_conditions."""


@test.skip("zwave_js: sibling test pending tryke port")
async def node_status_state() -> None:
    """Stub for test_node_status_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def config_parameter_state() -> None:
    """Stub for test_config_parameter_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def value_state() -> None:
    """Stub for test_value_state."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_condition_capabilities_node_status() -> None:
    """Stub for test_get_condition_capabilities_node_status."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_condition_capabilities_value() -> None:
    """Stub for test_get_condition_capabilities_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_condition_capabilities_config_parameter() -> None:
    """Stub for test_get_condition_capabilities_config_parameter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def failure_scenarios() -> None:
    """Stub for test_failure_scenarios."""


@test.skip("zwave_js: sibling test pending tryke port")
async def get_value_from_config_failure() -> None:
    """Stub for test_get_value_from_config_failure."""


@test.skip("zwave_js: sibling test pending tryke port")
async def condition_schema_coerces_string_command_class() -> None:
    """Stub for test_condition_schema_coerces_string_command_class."""
