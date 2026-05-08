"""Tryke skip-stubs for test_number.py - indirect parametrize unsupported."""

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
async def number_entity_availability() -> None:
    """Stub for test_number_entity_availability."""

@test.skip("indirect parametrize unsupported")
async def number_entity_functionality() -> None:
    """Stub for test_number_entity_functionality."""

@test.skip("indirect parametrize unsupported")
async def fetch_constraints_after_rate_limit_error() -> None:
    """Stub for test_fetch_constraints_after_rate_limit_error."""

@test.skip("indirect parametrize unsupported")
async def number_entity_error() -> None:
    """Stub for test_number_entity_error."""

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
