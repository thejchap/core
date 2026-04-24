"""Tryke fixtures for PurpleAir tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from aiopurpleair.endpoints.sensors import NearbySensorResult
from aiopurpleair.models.sensors import GetSensorsResponse
from tryke import Depends, fixture

from homeassistant.components.purpleair.const import DOMAIN
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry, load_fixture
from tests.hass_fixtures import hass as hass_fixture

TEST_API_KEY = "abcde12345"
TEST_SENSOR_INDEX1 = 123456
TEST_SENSOR_INDEX2 = 567890


@fixture
def get_sensors_response() -> GetSensorsResponse:
    """Mock an aiopurpleair GetSensorsResponse object."""
    return GetSensorsResponse.model_validate_json(
        load_fixture("get_sensors_response.json", "purpleair")
    )


@fixture
def api(
    get_sensors_response: GetSensorsResponse = Depends(get_sensors_response),
) -> Mock:
    """Return a mocked aiopurpleair API object."""
    return Mock(
        async_check_api_key=AsyncMock(),
        get_map_url=Mock(return_value="http://example.com"),
        sensors=Mock(
            async_get_nearby_sensors=AsyncMock(
                return_value=[
                    NearbySensorResult(sensor=sensor, distance=1.0)
                    for sensor in get_sensors_response.data.values()
                ]
            ),
            async_get_sensors=AsyncMock(return_value=get_sensors_response),
        ),
    )


@fixture
def config_entry_data() -> dict[str, Any]:
    """Return default config entry data."""
    return {"api_key": TEST_API_KEY}


@fixture
def config_entry_options() -> dict[str, Any]:
    """Return default config entry options."""
    return {"sensor_indices": [TEST_SENSOR_INDEX1]}


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    data: dict[str, Any] = Depends(config_entry_data),
    options: dict[str, Any] = Depends(config_entry_options),
) -> MockConfigEntry:
    """Create config entry and add to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="abcde",
        unique_id=TEST_API_KEY,
        data=data,
        options=options,
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def mock_aiopurpleair(api: Mock = Depends(api)) -> Generator[Mock]:
    """Patch aiopurpleair API."""
    with (
        patch("homeassistant.components.purpleair.config_flow.API", return_value=api),
        patch("homeassistant.components.purpleair.coordinator.API", return_value=api),
    ):
        yield api


@fixture
def mock_zeroconf() -> Generator[MagicMock]:
    """Mock zeroconf."""
    from zeroconf import DNSCache  # noqa: PLC0415

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch(
            "homeassistant.components.zeroconf.discovery.AsyncServiceBrowser",
        ) as mock_browser,
    ):
        asb = mock_browser.return_value
        asb.async_cancel = AsyncMock()
        zc = mock_zc.return_value
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def mock_async_zeroconf(
    _zc: MagicMock = Depends(mock_zeroconf),
) -> Generator[MagicMock]:
    """Mock AsyncZeroconf."""
    from zeroconf import DNSCache, Zeroconf  # noqa: PLC0415
    from zeroconf.asyncio import AsyncZeroconf  # noqa: PLC0415

    with patch(
        "homeassistant.components.zeroconf.HaAsyncZeroconf", spec=AsyncZeroconf
    ) as mock_aiozc:
        zc = mock_aiozc.return_value
        zc.async_unregister_service = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.zeroconf = Mock(spec=Zeroconf)
        zc.zeroconf.async_wait_for_start = AsyncMock()
        zc.zeroconf.cache = DNSCache()
        zc.zeroconf.done = False
        zc.async_close = AsyncMock()
        zc.ha_async_close = AsyncMock()
        yield zc


@fixture
async def setup_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _api: Mock = Depends(mock_aiopurpleair),
) -> None:
    """Set up purpleair."""
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
