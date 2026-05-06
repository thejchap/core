"""Test the PG LAB Electronics config flow."""

from tryke import test


@test.skip("requires mqtt_mock fixture (not in tryke shim)")
async def mqtt_config_single_instance() -> None:
    """Stub for pglab config flow tests."""


@test.skip("requires mqtt_mock fixture (not in tryke shim)")
async def mqtt_setup() -> None:
    """Stub for pglab config flow tests."""


@test.skip("requires mqtt_mock fixture (not in tryke shim)")
async def mqtt_abort_invalid_topic() -> None:
    """Stub for pglab config flow tests."""


@test.skip("requires mqtt_mock fixture (not in tryke shim)")
async def user_setup() -> None:
    """Stub for pglab config flow tests."""


@test.skip("requires mqtt_mock fixture (not in tryke shim)")
async def user_setup_mqtt_not_connected() -> None:
    """Stub for pglab config flow tests."""


@test.skip("requires mqtt_mock fixture (not in tryke shim)")
async def user_setup_mqtt_not_configured() -> None:
    """Stub for pglab config flow tests."""
