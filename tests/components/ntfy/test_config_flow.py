"""Tryke skip-stubs for ntfy config flow tests.

Original tests use complex fixture chain not yet ported to tryke shim; full port deferred.
"""

from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def form() -> None:
    """Stub for test_form (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def form_errors() -> None:
    """Stub for test_form_errors (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def form_already_configured() -> None:
    """Stub for test_form_already_configured (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def add_topic_flow() -> None:
    """Stub for test_add_topic_flow (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def generated_topic() -> None:
    """Stub for test_generated_topic (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def invalid_topic() -> None:
    """Stub for test_invalid_topic (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def topic_already_configured() -> None:
    """Stub for test_topic_already_configured (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reauth() -> None:
    """Stub for test_flow_reauth (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def form_reauth_errors() -> None:
    """Stub for test_form_reauth_errors (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reauth_account_mismatch() -> None:
    """Stub for test_flow_reauth_account_mismatch (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reconfigure() -> None:
    """Stub for test_flow_reconfigure (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reconfigure_token() -> None:
    """Stub for test_flow_reconfigure_token (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reconfigure_errors() -> None:
    """Stub for test_flow_reconfigure_errors (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reconfigure_already_configured() -> None:
    """Stub for test_flow_reconfigure_already_configured (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def flow_reconfigure_account_mismatch() -> None:
    """Stub for test_flow_reconfigure_account_mismatch (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def topic_reconfigure_flow() -> None:
    """Stub for test_topic_reconfigure_flow (port deferred)."""
