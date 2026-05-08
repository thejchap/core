"""Tryke skip-stubs for test_switch.py - indirect parametrize unsupported."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the home_connect integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.home_connect.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("home_connect")


@test.skip("indirect parametrize unsupported")
async def paired_depaired_devices_flow() -> None:
    """Stub for test_paired_depaired_devices_flow."""

@test.skip("indirect parametrize unsupported")
async def connected_devices() -> None:
    """Stub for test_connected_devices."""

@test.skip("indirect parametrize unsupported")
async def switch_entity_availability() -> None:
    """Stub for test_switch_entity_availability."""

@test.skip("indirect parametrize unsupported")
async def switch_functionality() -> None:
    """Stub for test_switch_functionality."""

@test.skip("indirect parametrize unsupported")
async def switch_exception_handling() -> None:
    """Stub for test_switch_exception_handling."""

@test.skip("indirect parametrize unsupported")
async def ent_desc_switch_functionality() -> None:
    """Stub for test_ent_desc_switch_functionality."""

@test.skip("indirect parametrize unsupported")
async def ent_desc_switch_exception_handling() -> None:
    """Stub for test_ent_desc_switch_exception_handling."""

@test.skip("indirect parametrize unsupported")
async def power_switch() -> None:
    """Stub for test_power_switch."""

@test.skip("indirect parametrize unsupported")
async def power_switch_fetch_off_state_from_current_value() -> None:
    """Stub for test_power_switch_fetch_off_state_from_current_value."""

@test.skip("indirect parametrize unsupported")
async def power_switch_service_validation_errors() -> None:
    """Stub for test_power_switch_service_validation_errors."""

@test.skip("indirect parametrize unsupported")
async def options_functionality() -> None:
    """Stub for test_options_functionality."""

@test.skip("indirect parametrize unsupported")
async def options_unavailable_when_option_is_missing() -> None:
    """Stub for test_options_unavailable_when_option_is_missing."""

@test.skip("indirect parametrize unsupported")
async def options_available_when_program_is_null() -> None:
    """Stub for test_options_available_when_program_is_null."""

@test.skip("indirect parametrize unsupported")
async def restore_option_entity() -> None:
    """Stub for test_restore_option_entity."""
