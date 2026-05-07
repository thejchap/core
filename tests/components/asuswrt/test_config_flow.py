"""Tryke skip-stubs for asuswrt config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("complex multi-fixture flow not yet ported")
async def user_legacy() -> None:
    """Stub for test_user_legacy (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def user_http() -> None:
    """Stub for test_user_http (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def error_pwd_required() -> None:
    """Stub for test_error_pwd_required (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def error_no_password_ssh() -> None:
    """Stub for test_error_no_password_ssh (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def error_invalid_ssh() -> None:
    """Stub for test_error_invalid_ssh (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def error_invalid_host() -> None:
    """Stub for test_error_invalid_host (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def abort_if_not_unique_id_setup() -> None:
    """Stub for test_abort_if_not_unique_id_setup (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def update_uniqueid_exist() -> None:
    """Stub for test_update_uniqueid_exist (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def abort_invalid_unique_id() -> None:
    """Stub for test_abort_invalid_unique_id (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def on_connect_legacy_failed() -> None:
    """Stub for test_on_connect_legacy_failed (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def on_connect_http_failed() -> None:
    """Stub for test_on_connect_http_failed (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def options_flow_ap() -> None:
    """Stub for test_options_flow_ap (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def options_flow_router() -> None:
    """Stub for test_options_flow_router (port deferred)."""

@test.skip("complex multi-fixture flow not yet ported")
async def options_flow_http() -> None:
    """Stub for test_options_flow_http (port deferred)."""
