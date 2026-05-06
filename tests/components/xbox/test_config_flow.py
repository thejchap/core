"""Test the xbox config flow."""

from tryke import test


@test.skip("requires aioclient_mock + hass_client fixtures")
async def full_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def discovery() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def form_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def form_already_configured_as_subentry() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def add_friend_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def add_friend_flow_already_configured() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def add_friend_flow_already_configured_as_entry() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def add_friend_flow_no_friends() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def add_friend_flow_config_entry_not_loaded() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def unique_id_and_friends_migration() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def migration_exceptions() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def migration_implementation_unavailable() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def flow_reauth() -> None:
    """Skipped pending fixture port."""

@test.skip("requires aioclient_mock + hass_client fixtures")
async def flow_reauth_unique_id_mismatch() -> None:
    """Skipped pending fixture port."""
