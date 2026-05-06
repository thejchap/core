"""Tryke skip-stubs for enphase_envoy config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_no_serial_number() -> None:
    """Stub for test_user_no_serial_number (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_errors() -> None:
    """Stub for test_form_errors (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf() -> None:
    """Stub for test_zeroconf (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_host_already_exists() -> None:
    """Stub for test_form_host_already_exists (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_serial_already_exists() -> None:
    """Stub for test_zeroconf_serial_already_exists (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_serial_already_exists_ignores_ipv6() -> None:
    """Stub for test_zeroconf_serial_already_exists_ignores_ipv6 (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zeroconf_host_already_exists() -> None:
    """Stub for test_zeroconf_host_already_exists (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zero_conf_while_form() -> None:
    """Stub for test_zero_conf_while_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zero_conf_second_envoy_while_form() -> None:
    """Stub for test_zero_conf_second_envoy_while_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zero_conf_old_blank_entry() -> None:
    """Stub for test_zero_conf_old_blank_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zero_conf_old_blank_entry_standard_title() -> None:
    """Stub for test_zero_conf_old_blank_entry_standard_title (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def zero_conf_old_blank_entry_user_title() -> None:
    """Stub for test_zero_conf_old_blank_entry_user_title (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_default() -> None:
    """Stub for test_options_default (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def options_set() -> None:
    """Stub for test_options_set (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure() -> None:
    """Stub for test_reconfigure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_nochange() -> None:
    """Stub for test_reconfigure_nochange (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_otherenvoy() -> None:
    """Stub for test_reconfigure_otherenvoy (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_auth_failure() -> None:
    """Stub for test_reconfigure_auth_failure (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reconfigure_change_ip_to_existing() -> None:
    """Stub for test_reconfigure_change_ip_to_existing (port deferred)."""
