"""Tryke fixtures for Husqvarna Automower tests."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
import time
from unittest.mock import AsyncMock, create_autospec, patch

from aioautomower.commands import MowerCommands, WorkAreaSettings
from aioautomower.model import MowerAttributes
from aioautomower.utils import mower_list_to_dictionary_dataclass
from aiohttp import ClientWebSocketResponse
from tryke import Depends, fixture

from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.components.husqvarna_automower.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from .const import CLIENT_ID, CLIENT_SECRET, USER_ID

from tests.common import MockConfigEntry, load_fixture, load_json_value_fixture
from tests.hass_fixtures import hass as hass_fx


@fixture
def jwt() -> str:
    """Load JWT fixture data."""
    return load_fixture("jwt", DOMAIN)


@fixture
def expires_at() -> float:
    """Set the OAuth token expiration timestamp."""
    return time.time() + 3600


@fixture
def scope() -> str:
    """Set the scope for the token."""
    return "iam:read amc:api"


@fixture
async def mower_time_zone() -> object:
    """Get the mower time zone."""
    return await dt_util.async_get_time_zone("Europe/Berlin")


@fixture
def values(
    mower_time_zone: object = Depends(mower_time_zone),
) -> dict[str, MowerAttributes]:
    """Load mower attribute values from fixture."""
    return mower_list_to_dictionary_dataclass(
        load_json_value_fixture("mower.json", DOMAIN),
        mower_time_zone,
    )


@fixture
def mock_config_entry(
    jwt: str = Depends(jwt),
    expires_at: float = Depends(expires_at),
    scope: str = Depends(scope),
) -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Husqvarna Automower of Erika Mustermann",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": jwt,
                "scope": scope,
                "expires_in": 86399,
                "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
                "provider": "husqvarna",
                "user_id": USER_ID,
                "token_type": "Bearer",
                "expires_at": expires_at,
            },
        },
        unique_id=USER_ID,
        entry_id="automower_test",
    )


@fixture
async def setup_credentials(hass: HomeAssistant = Depends(hass_fx)) -> None:
    """Set up application credentials."""
    await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
        DOMAIN,
    )


@fixture
def mock_automower_client(
    values: dict[str, MowerAttributes] = Depends(values),
) -> Generator[AsyncMock]:
    """Mock a Husqvarna Automower client."""

    async def listen() -> None:
        listen_block = asyncio.Event()
        await listen_block.wait()
        raise AssertionError("Listen was not cancelled!")

    with patch(
        "homeassistant.components.husqvarna_automower.AutomowerSession",
        autospec=True,
        spec_set=True,
    ) as mock:
        mock_instance = mock.return_value
        mock_instance.auth = AsyncMock(side_effect=ClientWebSocketResponse)
        mock_instance.get_status = AsyncMock(return_value=values)
        mock_instance.start_listening = AsyncMock(side_effect=listen)
        mock_instance.commands = create_autospec(
            MowerCommands, instance=True, spec_set=True
        )
        mock_instance.commands.workarea_settings.return_value = create_autospec(
            WorkAreaSettings, instance=True, spec_set=True
        )
        yield mock_instance
