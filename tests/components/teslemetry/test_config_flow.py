"""Test the Teslemetry config flow."""

from tryke import test


@test.skip("requires aioclient_mock + hass_client fixtures")
async def oauth_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauth() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauth_account_mismatch() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def duplicate_unique_id_abort() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def oauth_error_handling() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reconfigure() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reconfigure_account_mismatch() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reconfigure_oauth_error_handling() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reconfigure_oauth_error_recovery() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def migrate_error_from_future() -> None:
    """Skipped pending fixture port."""
