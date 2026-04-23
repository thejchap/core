"""Define test fixtures for AirVisual."""

from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.airvisual import (
    CONF_CITY,
    CONF_INTEGRATION_TYPE,
    DOMAIN,
    INTEGRATION_TYPE_GEOGRAPHY_COORDS,
)
from homeassistant.components.airvisual.config_flow import async_get_geography_id
from homeassistant.const import (
    CONF_API_KEY,
    CONF_COUNTRY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_SHOW_ON_MAP,
    CONF_STATE,
)
from homeassistant.core import HomeAssistant
from homeassistant.util.json import JsonObjectType

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass

TEST_API_KEY = "abcde12345"
TEST_LATITUDE = 51.528308
TEST_LONGITUDE = -0.3817765
TEST_LATITUDE2 = 37.514626
TEST_LONGITUDE2 = 127.057414

COORDS_CONFIG = {
    CONF_API_KEY: TEST_API_KEY,
    CONF_LATITUDE: TEST_LATITUDE,
    CONF_LONGITUDE: TEST_LONGITUDE,
}

COORDS_CONFIG2 = {
    CONF_API_KEY: TEST_API_KEY,
    CONF_LATITUDE: TEST_LATITUDE2,
    CONF_LONGITUDE: TEST_LONGITUDE2,
}

TEST_CITY = "Beijing"
TEST_STATE = "Beijing"
TEST_COUNTRY = "China"

NAME_CONFIG = {
    CONF_API_KEY: TEST_API_KEY,
    CONF_CITY: TEST_CITY,
    CONF_STATE: TEST_STATE,
    CONF_COUNTRY: TEST_COUNTRY,
}


@fixture
def data_cloud() -> JsonObjectType:
    """Define an update coordinator data example."""
    return load_json_object_fixture("data.json", "airvisual")


@fixture
def data_pro() -> JsonObjectType:
    """Define an update coordinator data example for the Pro."""
    return load_json_object_fixture("data.json", "airvisual_pro")


@fixture
def cloud_api(data_cloud: JsonObjectType = Depends(data_cloud)) -> Mock:
    """Define a mock CloudAPI object."""
    return Mock(
        air_quality=Mock(
            city=AsyncMock(return_value=data_cloud),
            nearest_city=AsyncMock(return_value=data_cloud),
        )
    )


@fixture
def node_samba(data_pro: JsonObjectType = Depends(data_pro)) -> Mock:
    """Define a mock NodeSamba object."""
    return Mock(
        async_connect=AsyncMock(),
        async_disconnect=AsyncMock(),
        async_get_latest_measurements=AsyncMock(return_value=data_pro),
    )


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return COORDS_CONFIG


@fixture
def integration_type() -> str:
    """Define an integration type."""
    return INTEGRATION_TYPE_GEOGRAPHY_COORDS


@fixture
def config_entry_version() -> int:
    """Define a config entry version fixture."""
    return 2


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass),
    config: dict[str, Any] = Depends(config),
    config_entry_version: int = Depends(config_entry_version),
    integration_type: str = Depends(integration_type),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="3bd2acb0e4f0476d40865546d0d91921",
        unique_id=async_get_geography_id(config),
        data={**config, CONF_INTEGRATION_TYPE: integration_type},
        options={CONF_SHOW_ON_MAP: True},
        version=config_entry_version,
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def mock_pyairvisual(
    cloud_api: Mock = Depends(cloud_api),
    node_samba: Mock = Depends(node_samba),
) -> AsyncGenerator[None]:
    """Define a fixture to patch pyairvisual."""
    with (
        patch(
            "homeassistant.components.airvisual.CloudAPI",
            return_value=cloud_api,
        ),
        patch(
            "homeassistant.components.airvisual.config_flow.CloudAPI",
            return_value=cloud_api,
        ),
        patch(
            "homeassistant.components.airvisual_pro.NodeSamba",
            return_value=node_samba,
        ),
        patch(
            "homeassistant.components.airvisual_pro.config_flow.NodeSamba",
            return_value=node_samba,
        ),
    ):
        yield


@fixture
async def setup_config_entry(
    hass: HomeAssistant = Depends(hass),
    config_entry: MockConfigEntry = Depends(config_entry),
    _mock_pyairvisual: None = Depends(mock_pyairvisual),
) -> None:
    """Define a fixture to set up airvisual."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.airvisual.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


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
