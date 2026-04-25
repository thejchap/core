"""Tryke fixtures for WattTime tests."""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, fixture

from homeassistant.components.watttime.config_flow import (
    CONF_LOCATION_TYPE,
    LOCATION_TYPE_COORDINATES,
)
from homeassistant.components.watttime.const import (
    CONF_BALANCING_AUTHORITY,
    CONF_BALANCING_AUTHORITY_ABBREV,
    DOMAIN,
)
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.json import JsonObjectType

from tests.common import MockConfigEntry, load_json_object_fixture


@fixture
def data_grid_region() -> JsonObjectType:
    """Define grid region data."""
    return load_json_object_fixture("grid_region_data.json", "watttime")


@fixture
def data_realtime_emissions() -> JsonObjectType:
    """Define realtime emissions data."""
    return load_json_object_fixture("realtime_emissions_data.json", "watttime")


@fixture
def get_grid_region(
    data_grid_region: JsonObjectType = Depends(data_grid_region),
) -> AsyncMock:
    """Define an aiowatttime method to get grid region data."""
    return AsyncMock(return_value=data_grid_region)


@fixture
def client(
    get_grid_region: AsyncMock = Depends(get_grid_region),
    data_realtime_emissions: JsonObjectType = Depends(data_realtime_emissions),
) -> Mock:
    """Define an aiowatttime client."""
    client = Mock()
    client.emissions.async_get_grid_region = get_grid_region
    client.emissions.async_get_realtime_emissions = AsyncMock(
        return_value=data_realtime_emissions
    )
    return client


@fixture
def config_auth() -> dict[str, Any]:
    """Define an auth config entry data fixture."""
    return {
        CONF_USERNAME: "user",
        CONF_PASSWORD: "password",
    }


@fixture
def config_coordinates() -> dict[str, Any]:
    """Define a coordinates config entry data fixture."""
    return {
        CONF_LATITUDE: 32.87336,
        CONF_LONGITUDE: -117.22743,
    }


@fixture
def config_location_type() -> dict[str, Any]:
    """Define a location type config entry data fixture."""
    return {
        CONF_LOCATION_TYPE: LOCATION_TYPE_COORDINATES,
    }


def make_config_entry(
    config_auth: dict[str, Any], config_coordinates: dict[str, Any]
) -> MockConfigEntry:
    """Build a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=(
            f"{config_coordinates[CONF_LATITUDE]}, {config_coordinates[CONF_LONGITUDE]}"
        ),
        data={
            **config_auth,
            **config_coordinates,
            CONF_BALANCING_AUTHORITY: "PJM New Jersey",
            CONF_BALANCING_AUTHORITY_ABBREV: "PJM_NJ",
        },
    )


@asynccontextmanager
async def setup_watttime(
    hass: HomeAssistant,
    client: Mock,
    config_auth: dict[str, Any],
    config_coordinates: dict[str, Any],
):
    """Set up WattTime keeping login patches active for the body."""
    with (
        patch(
            "homeassistant.components.watttime.Client.async_login", return_value=client
        ),
        patch(
            "homeassistant.components.watttime.config_flow.Client.async_login",
            return_value=client,
        ),
        patch("homeassistant.components.watttime.PLATFORMS", []),
    ):
        await async_setup_component(
            hass, DOMAIN, {**config_auth, **config_coordinates}
        )
        await hass.async_block_till_done()
        yield
