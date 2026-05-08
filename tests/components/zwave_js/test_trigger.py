"""Tryke skip-stubs for test_trigger.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_value_updated() -> None:
    """Stub for test_zwave_js_value_updated."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_value_updated_bypass_dynamic_validation() -> None:
    """Stub for test_zwave_js_value_updated_bypass_dynamic_validation."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_value_updated_bypass_dynamic_validation_no_nodes() -> None:
    """Stub for test_zwave_js_value_updated_bypass_dynamic_validation_no_nodes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_value_updated_bypass_dynamic_validation_no_driver() -> None:
    """Stub for test_zwave_js_value_updated_bypass_dynamic_validation_no_driver."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_event() -> None:
    """Stub for test_zwave_js_event."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_event_bypass_dynamic_validation() -> None:
    """Stub for test_zwave_js_event_bypass_dynamic_validation."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_event_bypass_dynamic_validation_no_nodes() -> None:
    """Stub for test_zwave_js_event_bypass_dynamic_validation_no_nodes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_event_invalid_config_entry_id() -> None:
    """Stub for test_zwave_js_event_invalid_config_entry_id."""


@test.skip("zwave_js: sibling test pending tryke port")
async def invalid_trigger_configs() -> None:
    """Stub for test_invalid_trigger_configs."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_trigger_config_entry_unloaded() -> None:
    """Stub for test_zwave_js_trigger_config_entry_unloaded."""


@test.skip("zwave_js: sibling test pending tryke port")
async def server_reconnect_event() -> None:
    """Stub for test_server_reconnect_event."""


@test.skip("zwave_js: sibling test pending tryke port")
async def server_reconnect_value_updated() -> None:
    """Stub for test_server_reconnect_value_updated."""


@test.skip("zwave_js: sibling test pending tryke port")
async def zwave_js_old_syntax() -> None:
    """Stub for test_zwave_js_old_syntax."""
