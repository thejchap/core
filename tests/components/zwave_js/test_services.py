"""Tryke skip-stubs for test_services.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_config_parameter() -> None:
    """Stub for test_set_config_parameter."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_config_parameter_gather() -> None:
    """Stub for test_set_config_parameter_gather."""


@test.skip("zwave_js: sibling test pending tryke port")
async def bulk_set_config_parameters() -> None:
    """Stub for test_bulk_set_config_parameters."""


@test.skip("zwave_js: sibling test pending tryke port")
async def bulk_set_config_parameters_gather() -> None:
    """Stub for test_bulk_set_config_parameters_gather."""


@test.skip("zwave_js: sibling test pending tryke port")
async def refresh_value() -> None:
    """Stub for test_refresh_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_value() -> None:
    """Stub for test_set_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_value_string() -> None:
    """Stub for test_set_value_string."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_value_options() -> None:
    """Stub for test_set_value_options."""


@test.skip("zwave_js: sibling test pending tryke port")
async def set_value_gather() -> None:
    """Stub for test_set_value_gather."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multicast_set_value() -> None:
    """Stub for test_multicast_set_value."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multicast_set_value_options() -> None:
    """Stub for test_multicast_set_value_options."""


@test.skip("zwave_js: sibling test pending tryke port")
async def multicast_set_value_string() -> None:
    """Stub for test_multicast_set_value_string."""


@test.skip("zwave_js: sibling test pending tryke port")
async def ping() -> None:
    """Stub for test_ping."""


@test.skip("zwave_js: sibling test pending tryke port")
async def invoke_cc_api() -> None:
    """Stub for test_invoke_cc_api."""


@test.skip("zwave_js: sibling test pending tryke port")
async def refresh_notifications() -> None:
    """Stub for test_refresh_notifications."""
