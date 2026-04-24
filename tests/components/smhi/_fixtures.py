"""Tryke fixtures for SMHI config flow tests."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from pysmhi.smhi_fire_forecast import SMHIFireForecast, SMHIFirePointForecast
from pysmhi.smhi_forecast import SMHIForecast, SMHIPointForecast
from tryke import Depends, fixture

from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from tests.common import load_fixture
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

from . import TEST_CONFIG


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.smhi.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def load_data() -> tuple[str, str, str, str]:
    """Load fixture data."""
    return (
        load_fixture("smhi.json", "smhi"),
        load_fixture("smhi_night.json", "smhi"),
        load_fixture("smhi_short.json", "smhi"),
        load_fixture("smhi_fire.json", "smhi"),
    )


@fixture
def load_json(
    data: tuple[str, str, str, str] = Depends(load_data),
) -> dict[str, Any]:
    """Load forecast JSON."""
    return json.loads(data[0])


@fixture
def load_fire_json(
    data: tuple[str, str, str, str] = Depends(load_data),
) -> dict[str, Any]:
    """Load fire forecast JSON."""
    return json.loads(data[3])


@fixture
async def get_data(
    hass: HomeAssistant = Depends(hass_fixture),
    mocker: AiohttpClientMocker = Depends(aioclient_mock),
    forecast_json: dict[str, Any] = Depends(load_json),
) -> AsyncGenerator[tuple[list[SMHIForecast], list[SMHIForecast], list[SMHIForecast]]]:
    """Build forecast data via the real SMHIPointForecast client."""
    client = SMHIPointForecast(
        TEST_CONFIG[CONF_LOCATION][CONF_LONGITUDE],
        TEST_CONFIG[CONF_LOCATION][CONF_LATITUDE],
        mocker.create_session(hass.loop),
    )
    with patch.object(
        client._api,
        "async_get_data",
        return_value=forecast_json,
    ):
        data_daily = await client.async_get_daily_forecast()
        data_twice_daily = await client.async_get_twice_daily_forecast()
        data_hourly = await client.async_get_hourly_forecast()

    yield (data_daily, data_twice_daily, data_hourly)
    await client._api._session.close()


@fixture
async def get_fire_data(
    hass: HomeAssistant = Depends(hass_fixture),
    mocker: AiohttpClientMocker = Depends(aioclient_mock),
    fire_json: dict[str, Any] = Depends(load_fire_json),
) -> AsyncGenerator[tuple[list[SMHIFireForecast], list[SMHIFireForecast]]]:
    """Build fire-forecast data via the real SMHIFirePointForecast client."""
    from freezegun import freeze_time

    client = SMHIFirePointForecast(
        TEST_CONFIG[CONF_LOCATION][CONF_LONGITUDE],
        TEST_CONFIG[CONF_LOCATION][CONF_LATITUDE],
        mocker.create_session(hass.loop),
    )
    with (
        freeze_time("2025-10-03"),
        patch.object(client._api, "async_get_data", return_value=fire_json),
    ):
        data_daily = await client.async_get_daily_forecast()
        data_hourly = await client.async_get_hourly_forecast()

    yield (data_daily, data_hourly)
    await client._api._session.close()


@fixture
async def mock_client(
    data: tuple[
        list[SMHIForecast], list[SMHIForecast], list[SMHIForecast]
    ] = Depends(get_data),
) -> AsyncGenerator[MagicMock]:
    """Mock SMHIPointForecast client."""
    with (
        patch(
            "homeassistant.components.smhi.coordinator.SMHIPointForecast",
            autospec=True,
        ) as mock_client,
        patch(
            "homeassistant.components.smhi.config_flow.SMHIPointForecast",
            return_value=mock_client.return_value,
        ),
    ):
        client = mock_client.return_value
        client.async_get_daily_forecast.return_value = data[0]
        client.async_get_twice_daily_forecast.return_value = data[1]
        client.async_get_hourly_forecast.return_value = data[2]
        yield client


@fixture
async def mock_fire_client(
    data: tuple[list[SMHIFireForecast], list[SMHIFireForecast]] = Depends(
        get_fire_data
    ),
) -> AsyncGenerator[MagicMock]:
    """Mock SMHIFirePointForecast client."""
    with patch(
        "homeassistant.components.smhi.coordinator.SMHIFirePointForecast",
        autospec=True,
    ) as mock_client:
        client = mock_client.return_value
        client.async_get_daily_forecast.return_value = data[0]
        client.async_get_hourly_forecast.return_value = data[1]
        yield client
