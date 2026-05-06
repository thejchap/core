"""Tests for the SmartThings config flow module."""

from tryke import test


@test.skip("requires OAuth2 hass_client fixtures")
async def full_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def not_enough_scopes() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def duplicate_entry() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def no_cloud() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def reauthentication() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def reauthentication_wrong_scopes() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def reauth_account_mismatch() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def reauthentication_no_cloud() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def migration() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def migration_wrong_location() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def migration_no_cloud() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def dhcp_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires OAuth2 hass_client fixtures")
async def duplicate_entry_dhcp() -> None:
    """Skipped pending fixture port."""
