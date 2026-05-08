"""Tryke skip-stubs for test_select.py - indirect parametrize unsupported."""

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
async def select_entity_availability() -> None:
    """Stub for test_select_entity_availability."""

@test.skip("indirect parametrize unsupported")
async def filter_programs() -> None:
    """Stub for test_filter_programs."""

@test.skip("indirect parametrize unsupported")
async def select_program_functionality() -> None:
    """Stub for test_select_program_functionality."""

@test.skip("indirect parametrize unsupported")
async def select_exception_handling() -> None:
    """Stub for test_select_exception_handling."""

@test.skip("indirect parametrize unsupported")
async def programs_updated_on_connect() -> None:
    """Stub for test_programs_updated_on_connect."""

@test.skip("indirect parametrize unsupported")
async def select_functionality() -> None:
    """Stub for test_select_functionality."""

@test.skip("indirect parametrize unsupported")
async def fetch_allowed_values() -> None:
    """Stub for test_fetch_allowed_values."""

@test.skip("indirect parametrize unsupported")
async def fetch_allowed_values_after_rate_limit_error() -> None:
    """Stub for test_fetch_allowed_values_after_rate_limit_error."""

@test.skip("indirect parametrize unsupported")
async def default_values_after_fetch_allowed_values_error() -> None:
    """Stub for test_default_values_after_fetch_allowed_values_error."""

@test.skip("indirect parametrize unsupported")
async def select_entity_error() -> None:
    """Stub for test_select_entity_error."""

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

@test.skip("indirect parametrize unsupported")
async def favorite_001_program_not_exposed_as_option() -> None:
    """Stub for test_favorite_001_program_not_exposed_as_option."""

@test.skip("indirect parametrize unsupported")
async def use_base_program_on_favorite_program() -> None:
    """Stub for test_use_base_program_on_favorite_program."""
