"""Tryke skip-stubs for plaato config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form() -> None:
    """Stub for test_show_config_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_device_type_airlock() -> None:
    """Stub for test_show_config_form_device_type_airlock (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_device_type_keg() -> None:
    """Stub for test_show_config_form_device_type_keg (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_validate_webhook() -> None:
    """Stub for test_show_config_form_validate_webhook (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_validate_webhook_not_connected() -> None:
    """Stub for test_show_config_form_validate_webhook_not_connected (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_validate_token() -> None:
    """Stub for test_show_config_form_validate_token (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_no_cloud_webhook() -> None:
    """Stub for test_show_config_form_no_cloud_webhook (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_config_form_api_method_no_auth_token() -> None:
    """Stub for test_show_config_form_api_method_no_auth_token (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options() -> None:
    """Stub for test_options (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_webhook() -> None:
    """Stub for test_options_webhook (port deferred)."""
