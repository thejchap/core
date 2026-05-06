"""Tests for Tibber config flow."""

from tryke import test


@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def oauth_create_entry_abort_exceptions() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def oauth_create_entry_connection_error_retry() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def data_api_requires_credentials() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def data_api_extra_authorize_scope() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def full_flow_success() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def data_api_abort_when_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def reauth_flow_success() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + recorder_mock fixtures")
async def reauth_flow_wrong_account() -> None:
    """Skipped pending fixture port."""
