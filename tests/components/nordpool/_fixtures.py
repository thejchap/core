"""Tryke fixtures for Nord Pool tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
import json
from typing import Any

from pynordpool import API, NordPoolClient
from tryke import Depends, fixture

from homeassistant.components.nordpool.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.components.nordpool import ENTRY_CONFIG
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def load_data() -> list[str]:
    """Load fixture files and return their raw text."""
    return [
        load_fixture("delivery_period_today.json", DOMAIN),
        load_fixture("delivery_period_yesterday.json", DOMAIN),
        load_fixture("delivery_period_tomorrow.json", DOMAIN),
    ]


@fixture
def load_json(
    load_data_: list[str] = Depends(load_data),
) -> list[dict[str, Any]]:
    """Load fixture with json data and return."""
    return [
        json.loads(load_data_[0]),
        json.loads(load_data_[1]),
        json.loads(load_data_[2]),
    ]


@fixture
async def get_client(
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient_mock_: AiohttpClientMocker = Depends(aioclient_mock),
    load_json_: list[dict[str, Any]] = Depends(load_json),
) -> AsyncGenerator[NordPoolClient]:
    """Retrieve data from Nord Pool library."""
    aioclient_mock_.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=load_json_[0],
    )
    aioclient_mock_.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-01",
            "market": "DayAhead",
            "deliveryArea": "SE3",
            "currency": "EUR",
        },
        json=load_json_[0],
    )
    aioclient_mock_.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-09-30",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=load_json_[1],
    )
    aioclient_mock_.request(
        "GET",
        url=API + "/DayAheadPrices",
        params={
            "date": "2025-10-02",
            "market": "DayAhead",
            "deliveryArea": "SE3,SE4",
            "currency": "SEK",
        },
        json=load_json_[2],
    )
    client = NordPoolClient(aioclient_mock_.create_session(hass.loop))
    yield client
    await client._session.close()


@fixture
async def load_int(
    hass: HomeAssistant = Depends(hass_fixture),
    _client: NordPoolClient = Depends(get_client),
) -> MockConfigEntry:
    """Set up the Nord Pool integration in Home Assistant."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        data=ENTRY_CONFIG,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
