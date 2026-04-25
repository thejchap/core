"""Tryke fixtures for the Electric Kiwi integration."""

from __future__ import annotations

from collections.abc import Generator
from time import time
from unittest.mock import AsyncMock, patch

from electrickiwi_api.model import (
    AccountSummary,
    CustomerConnection,
    Hop,
    HopIntervals,
    Service,
    Session,
)
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.electric_kiwi.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_json_value_fixture
from tests.hass_fixtures import hass as hass_fx

CLIENT_ID = "1234"
CLIENT_SECRET = "5678"
REDIRECT_URI = "https://example.com/auth/external/callback"


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials component."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )


@fixture
def electrickiwi_api() -> Generator[AsyncMock]:
    """Mock ek api and return values."""
    with (
        patch(
            "homeassistant.components.electric_kiwi.ElectricKiwiApi",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.electric_kiwi.config_flow.ElectricKiwiApi",
            new=mock_client,
        ),
    ):
        client = mock_client.return_value
        client.customer_number = 123456
        client.electricity = Service(
            identifier="00000000DDA",
            service="electricity",
            service_status="Y",
            is_primary_service=True,
        )
        client.get_active_session.return_value = Session.from_dict(
            load_json_value_fixture("session.json", DOMAIN)
        )
        client.get_hop_intervals.return_value = HopIntervals.from_dict(
            load_json_value_fixture("hop_intervals.json", DOMAIN)
        )
        client.get_hop.return_value = Hop.from_dict(
            load_json_value_fixture("get_hop.json", DOMAIN)
        )
        client.get_account_summary.return_value = AccountSummary.from_dict(
            load_json_value_fixture("account_summary.json", DOMAIN)
        )
        client.get_connection_details.return_value = CustomerConnection.from_dict(
            load_json_value_fixture("connection_details.json", DOMAIN)
        )
        yield client


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.electric_kiwi.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def migrated_config_entry() -> MockConfigEntry:
    """Create mocked migrated config entry."""
    return MockConfigEntry(
        title="Electric Kiwi",
        domain=DOMAIN,
        data={
            "id": "123456",
            "auth_implementation": DOMAIN,
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "expires_at": time() + 60,
            },
        },
        unique_id="123456",
        version=1,
        minor_version=2,
    )
