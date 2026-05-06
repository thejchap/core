"""Tryke skip-stubs for octoprint config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def form_unknown_exception() -> None:
    """Stub for test_form_unknown_exception (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_zerconf_form() -> None:
    """Stub for test_show_zerconf_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def show_ssdp_form() -> None:
    """Stub for test_show_ssdp_form (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def import_yaml() -> None:
    """Stub for test_import_yaml (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def import_duplicate_yaml() -> None:
    """Stub for test_import_duplicate_yaml (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def failed_auth() -> None:
    """Stub for test_failed_auth (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def failed_auth_unexpected_error() -> None:
    """Stub for test_failed_auth_unexpected_error (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def user_duplicate_entry() -> None:
    """Stub for test_user_duplicate_entry (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def duplicate_zerconf_ignored() -> None:
    """Stub for test_duplicate_zerconf_ignored (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def duplicate_ssdp_ignored() -> None:
    """Stub for test_duplicate_ssdp_ignored (port deferred)."""

@test.skip("complex fixture chain not yet ported to tryke shim")
async def reauth_form() -> None:
    """Stub for test_reauth_form (port deferred)."""
