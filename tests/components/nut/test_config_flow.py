"""Tryke skip-stubs for nut config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_zeroconf() -> None:
    """Stub for test_form_zeroconf (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_user_one_alias() -> None:
    """Stub for test_form_user_one_alias (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_user_multiple_aliases() -> None:
    """Stub for test_form_user_multiple_aliases (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_user_one_alias_with_ignored_entry() -> None:
    """Stub for test_form_user_one_alias_with_ignored_entry (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_no_aliases_found() -> None:
    """Stub for test_form_no_aliases_found (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def form_cannot_connect() -> None:
    """Stub for test_form_cannot_connect (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def auth_failures() -> None:
    """Stub for test_auth_failures (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reauth() -> None:
    """Stub for test_reauth (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_if_already_setup() -> None:
    """Stub for test_abort_if_already_setup (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_duplicate_unique_ids() -> None:
    """Stub for test_abort_duplicate_unique_ids (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_multiple_aliases_duplicate_unique_ids() -> None:
    """Stub for test_abort_multiple_aliases_duplicate_unique_ids (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def abort_if_already_setup_alias() -> None:
    """Stub for test_abort_if_already_setup_alias (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_successful() -> None:
    """Stub for test_reconfigure_one_alias_successful (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_nochange() -> None:
    """Stub for test_reconfigure_one_alias_nochange (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_password_nochange() -> None:
    """Stub for test_reconfigure_one_alias_password_nochange (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_already_configured() -> None:
    """Stub for test_reconfigure_one_alias_already_configured (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_unique_id_change() -> None:
    """Stub for test_reconfigure_one_alias_unique_id_change (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_one_alias_duplicate_unique_ids() -> None:
    """Stub for test_reconfigure_one_alias_duplicate_unique_ids (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_successful() -> None:
    """Stub for test_reconfigure_multiple_aliases_successful (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_nochange() -> None:
    """Stub for test_reconfigure_multiple_aliases_nochange (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_password_nochange() -> None:
    """Stub for test_reconfigure_multiple_aliases_password_nochange (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_already_configured() -> None:
    """Stub for test_reconfigure_multiple_aliases_already_configured (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_unique_id_change() -> None:
    """Stub for test_reconfigure_multiple_aliases_unique_id_change (port deferred)."""

@test.skip("requires aionut + util.async_init_integration chain (not ported)")
async def reconfigure_multiple_aliases_duplicate_unique_ids() -> None:
    """Stub for test_reconfigure_multiple_aliases_duplicate_unique_ids (port deferred)."""
