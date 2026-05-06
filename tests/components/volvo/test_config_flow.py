"""Test the Volvo config flow."""

from tryke import test


@test.skip("requires aioclient_mock + hass_client fixtures")
async def full_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def single_vin_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauth_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reauth_no_stale_data() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def reconfigure_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def unique_id_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def api_failure_flow() -> None:
    """Skipped pending fixture port."""
