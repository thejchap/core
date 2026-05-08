"""Common helpers for the tesla_fleet integration tests."""

from __future__ import annotations

from unittest.mock import patch

import jwt
from tesla_fleet_api.const import Scope

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.tesla_fleet.const import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from homeassistant.core import State
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry

UID = "abc-123"
VIN = "LRWXF7EK4KC700000"
ENERGY_SITE_ID = "123456"


def get_state_by_unique_id(
    hass: HomeAssistant, platform: str, unique_id: str
) -> State | None:
    """Look up a state by entity_registry unique_id (avoids translation slug dependence)."""
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
    if entity_id is None:
        return None
    return hass.states.get(entity_id)


def create_config_entry(
    expires_at: int,
    scopes: list[Scope],
    implementation: str = DOMAIN,
    region: str = "NA",
) -> MockConfigEntry:
    """Create Tesla Fleet entry in Home Assistant."""
    access_token = jwt.encode(
        {
            "sub": UID,
            "aud": [],
            "scp": scopes,
            "ou_code": region,
        },
        key="",
        algorithm="none",
    )

    return MockConfigEntry(
        domain=DOMAIN,
        title=UID,
        unique_id=UID,
        data={
            "auth_implementation": implementation,
            "token": {
                "status": 0,
                "userid": UID,
                "access_token": access_token,
                "refresh_token": "mock-refresh-token",
                "expires_at": expires_at,
                "scope": ",".join(scopes),
            },
        },
    )


async def setup_platform(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platforms: list[Platform] | None = None,
) -> None:
    """Set up the Tesla Fleet platform."""

    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential("CLIENT_ID", "CLIENT_SECRET", "Home Assistant"),
        DOMAIN,
    )

    config_entry.add_to_hass(hass)

    if platforms is None:
        await hass.config_entries.async_setup(config_entry.entry_id)
    else:
        with patch("homeassistant.components.tesla_fleet.PLATFORMS", platforms):
            await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
