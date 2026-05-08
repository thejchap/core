"""Tryke skip-stubs for test_services.py - indirect parametrize unsupported."""

from tryke import expect, test


@test
def domain_const_importable() -> None:
    """Smoke test: the home_connect integration's DOMAIN constant imports cleanly."""
    from homeassistant.components.home_connect.const import DOMAIN  # noqa: PLC0415
    expect(DOMAIN).to_equal("home_connect")


@test.skip("indirect parametrize unsupported")
async def services_yaml_set_program_and_options_program_keys() -> None:
    """Stub for test_services_yaml_set_program_and_options_program_keys."""

@test.skip("indirect parametrize unsupported")
async def services_yaml_set_program_and_options_option_keys() -> None:
    """Stub for test_services_yaml_set_program_and_options_option_keys."""

@test.skip("indirect parametrize unsupported")
async def key_value_services() -> None:
    """Stub for test_key_value_services."""

@test.skip("indirect parametrize unsupported")
async def set_program_and_options() -> None:
    """Stub for test_set_program_and_options."""

@test.skip("indirect parametrize unsupported")
async def set_program_and_options_exceptions() -> None:
    """Stub for test_set_program_and_options_exceptions."""

@test.skip("indirect parametrize unsupported")
async def start_selected_program() -> None:
    """Stub for test_start_selected_program."""

@test.skip("indirect parametrize unsupported")
async def start_selected_program_and_options_exceptions() -> None:
    """Stub for test_start_selected_program_and_options_exceptions."""

@test.skip("indirect parametrize unsupported")
async def no_program_error() -> None:
    """Stub for test_no_program_error."""

@test.skip("indirect parametrize unsupported")
async def services_appliance_not_found() -> None:
    """Stub for test_services_appliance_not_found."""

@test.skip("indirect parametrize unsupported")
async def services_exception() -> None:
    """Stub for test_services_exception."""

@test.skip("indirect parametrize unsupported")
async def not_possible_to_use_favorite_program() -> None:
    """Stub for test_not_possible_to_use_favorite_program."""
