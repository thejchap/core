"""Test the Smhi config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from pysmhi import SmhiForecastException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.smhi.const import DOMAIN
from homeassistant.components.weather import DOMAIN as WEATHER_DOMAIN
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er

from ._fixtures import mock_client, mock_fire_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_client),
    _fire: MagicMock = Depends(mock_fire_client),
) -> None:
    """Test we get the form and create an entry."""
    hass.config.latitude = 0.0
    hass.config.longitude = 0.0

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.smhi.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_LOCATION: {CONF_LATITUDE: 0.0, CONF_LONGITUDE: 0.0}},
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Home")
    expect(result["result"].unique_id).to_equal("0.0-0.0")
    expect(result["data"]).to_equal(
        {"location": {"latitude": 0.0, "longitude": 0.0}}
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 1.0, CONF_LONGITUDE: 1.0}},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Weather 1.0 1.0")
    expect(result["data"]).to_equal(
        {"location": {"latitude": 1.0, "longitude": 1.0}}
    )


@test
async def form_invalid_coordinates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    _fire: MagicMock = Depends(mock_fire_client),
) -> None:
    """Test we handle invalid coordinates."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    client.async_get_daily_forecast.side_effect = SmhiForecastException

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 0.0, CONF_LONGITUDE: 0.0}},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "wrong_location"})

    client.async_get_daily_forecast.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 2.0, CONF_LONGITUDE: 2.0}},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Weather 2.0 2.0")
    expect(result["data"]).to_equal(
        {"location": {"latitude": 2.0, "longitude": 2.0}}
    )


@test
async def form_unique_id_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_client),
    _fire: MagicMock = Depends(mock_fire_client),
) -> None:
    """Test we handle unique id already exist."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="1.0-1.0",
        data={
            "location": {"latitude": 1.0, "longitude": 1.0},
            "name": "Weather",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 1.0, CONF_LONGITUDE: 1.0}},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_client),
    _fire: MagicMock = Depends(mock_fire_client),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test re-configuration flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="57.2898-13.6304",
        data={"location": {"latitude": 57.2898, "longitude": 13.6304}},
        version=3,
    )
    entry.add_to_hass(hass)

    entity = entity_registry.async_get_or_create(
        WEATHER_DOMAIN, DOMAIN, "57.2898, 13.6304"
    )
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "57.2898, 13.6304")},
        manufacturer="SMHI",
        model="v2",
        name=entry.title,
    )

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)

    client.async_get_daily_forecast.side_effect = SmhiForecastException

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 0.0, CONF_LONGITUDE: 0.0}},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "wrong_location"})

    client.async_get_daily_forecast.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 58.2898, CONF_LONGITUDE: 14.6304}},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry.title).to_equal("Home")
    expect(entry.unique_id).to_equal("58.2898-14.6304")
    expect(entry.data).to_equal(
        {"location": {"latitude": 58.2898, "longitude": 14.6304}}
    )
    entity = entity_registry.async_get(entity.entity_id)
    expect(entity is not None).to_be(True)
    expect(entity.unique_id).to_equal("58.2898, 14.6304")
    device = device_registry.async_get(device.id)
    expect(device is not None).to_be(True)
    expect(device.identifiers).to_equal({(DOMAIN, "58.2898, 14.6304")})
