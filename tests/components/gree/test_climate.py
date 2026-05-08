"""Tryke skip stub for test_climate.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the gree.climate module imports cleanly."""
    from homeassistant.components.gree import climate  # noqa: PLC0415
    expect(climate).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_called_once() -> None:
    """Stub for test_discovery_called_once."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_setup() -> None:
    """Stub for test_discovery_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_setup_connection_error() -> None:
    """Stub for test_discovery_setup_connection_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_after_setup() -> None:
    """Stub for test_discovery_after_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_add_device_after_setup() -> None:
    """Stub for test_discovery_add_device_after_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discovery_device_bind_after_setup() -> None:
    """Stub for test_discovery_device_bind_after_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_connection_failure() -> None:
    """Stub for test_update_connection_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_connection_send_failure_recovery() -> None:
    """Stub for test_update_connection_send_failure_recovery."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_unhandled_exception() -> None:
    """Stub for test_update_unhandled_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_command_device_timeout() -> None:
    """Stub for test_send_command_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unresponsive_device() -> None:
    """Stub for test_unresponsive_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_power_on() -> None:
    """Stub for test_send_power_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_power_off_device_timeout() -> None:
    """Stub for test_send_power_off_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_target_temperature() -> None:
    """Stub for test_send_target_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_target_temperature_with_hvac_mode() -> None:
    """Stub for test_send_target_temperature_with_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_target_temperature_device_timeout() -> None:
    """Stub for test_send_target_temperature_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_target_temperature() -> None:
    """Stub for test_update_target_temperature."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_preset_mode() -> None:
    """Stub for test_send_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_invalid_preset_mode() -> None:
    """Stub for test_send_invalid_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_preset_mode_device_timeout() -> None:
    """Stub for test_send_preset_mode_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_preset_mode() -> None:
    """Stub for test_update_preset_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_hvac_mode() -> None:
    """Stub for test_send_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_hvac_mode_device_timeout() -> None:
    """Stub for test_send_hvac_mode_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_hvac_mode() -> None:
    """Stub for test_update_hvac_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_fan_mode() -> None:
    """Stub for test_send_fan_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_invalid_fan_mode() -> None:
    """Stub for test_send_invalid_fan_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_fan_mode_device_timeout() -> None:
    """Stub for test_send_fan_mode_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_fan_mode() -> None:
    """Stub for test_update_fan_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_swing_mode() -> None:
    """Stub for test_send_swing_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_invalid_swing_mode() -> None:
    """Stub for test_send_invalid_swing_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def send_swing_mode_device_timeout() -> None:
    """Stub for test_send_swing_mode_device_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_swing_mode() -> None:
    """Stub for test_update_swing_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def coordinator_update_handler() -> None:
    """Stub for test_coordinator_update_handler."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def registry_settings() -> None:
    """Stub for test_registry_settings."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_states() -> None:
    """Stub for test_entity_states."""

