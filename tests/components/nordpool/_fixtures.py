"""Tryke fixtures for the Nord Pool integration."""

from collections.abc import AsyncGenerator
import json
from typing import Any
from unittest.mock import patch

from pynordpool import API, NordPoolClient
from tryke import Depends, fixture

from homeassistant.components.nordpool.const import DOMAIN, PLATFORMS
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import ENTRY_CONFIG

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def load_platforms() -> list[Platform]:
    """Return list of platforms to load."""
    return PLATFORMS


@fixture
def load_data() -> list[str]:
    """Load fixture with fixture data and return."""
    return [
        load_fixture("delivery_period_today.json", DOMAIN),
        load_fixture("delivery_period_yesterday.json", DOMAIN),
        load_fixture("delivery_period_tomorrow.json", DOMAIN),
    ]


@fixture
def load_json(
    data: list[str] = Depends(load_data),
) -> list[dict[str, Any]]:
    """Load fixture with json data and return."""
    return [
        json.loads(data[0]),
        json.loads(data[1]),
        json.loads(data[2]),
    ]


@fixture
async def get_client(
    hass: HomeAssistant = Depends(hass_fixture),
    aio: AiohttpClientMocker = Depends(aioclient_mock),
    json_data: list[dict[str, Any]] = Depends(load_json),
) -> AsyncGenerator[NordPoolClient]:
    """Retrieve data from Nord Pool library."""
    aio.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=json_data[0],
    )
    aio.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "SE3",
            "currency": "EUR",
        },
        json=json_data[0],
    )
    aio.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-09-30",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=json_data[1],
    )
    aio.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-02",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=json_data[2],
    )
    client = NordPoolClient(aio.create_session(hass.loop))
    yield client
    await client._session.close()


@fixture
async def load_int(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: NordPoolClient = Depends(get_client),
    platforms: list[Platform] = Depends(load_platforms),
) -> MockConfigEntry:
    """Set up the Nord Pool integration in Home Assistant."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=ENTRY_CONFIG,
    )

    config_entry.add_to_hass(hass)

    with patch("homeassistant.components.nordpool.PLATFORMS", platforms):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    return config_entry
