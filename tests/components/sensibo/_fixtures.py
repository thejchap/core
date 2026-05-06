"""Tryke fixtures for Sensibo integration tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from pysensibo import SensiboClient, SensiboData
from tryke import Depends, fixture

from homeassistant.core import HomeAssistant

from tests.common import load_fixture
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.sensibo.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def load_data() -> tuple[str, str]:
    """Load fixture with fixture data and return."""
    return (load_fixture("data.json", "sensibo"), load_fixture("me.json", "sensibo"))


@fixture
def load_json(
    data: tuple[str, str] = Depends(load_data),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load fixture with json data and return."""
    json_data: dict[str, Any] = json.loads(data[0])
    json_me: dict[str, Any] = json.loads(data[1])
    return (json_data, json_me)


@fixture
async def get_data(
    hass: HomeAssistant = Depends(hass_fixture),
    aio_mock: AiohttpClientMocker = Depends(aioclient_mock),
    json_data: tuple[dict[str, Any], dict[str, Any]] = Depends(load_json),
) -> AsyncGenerator[tuple[SensiboData, dict[str, Any], dict[str, Any]]]:
    """Get data from api."""
    client = SensiboClient("1234567890", aio_mock.create_session(hass.loop))
    with patch.object(
        client,
        "async_get_me",
        return_value=json_data[1],
    ):
        me = await client.async_get_me()
    with patch.object(
        client,
        "async_get_devices",
        return_value=json_data[0],
    ):
        data = await client.async_get_devices_data()
        raw_data = await client.async_get_devices()
    yield (data, me, raw_data)
    await client._session.close()


@fixture
async def mock_client(
    data: tuple[SensiboData, dict[str, Any], dict[str, Any]] = Depends(get_data),
) -> AsyncGenerator[MagicMock]:
    """Mock SensiboClient."""

    with (
        patch(
            "homeassistant.components.sensibo.coordinator.SensiboClient",
            autospec=True,
        ) as mock_client,
        patch("homeassistant.components.sensibo.util.SensiboClient", new=mock_client),
    ):
        client = mock_client.return_value
        client.async_get_devices_data.return_value = data[0]
        client.async_get_me.return_value = data[1]
        client.async_get_devices.return_value = data[2]
        yield client
