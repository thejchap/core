"""Test the Amber Electric Sensors."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    general_channel_and_controlled_load_config_entry,
    general_channel_and_feed_in_config_entry,
    general_channel_config_entry,
    mock_amber_client_general_and_controlled_load,
    mock_amber_client_general_and_feed_in,
    mock_amber_client_general_channel,
    mock_amber_client_general_channel_with_range,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fx, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def general_price_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_config_entry: MockConfigEntry = Depends(
        general_channel_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_channel),
) -> None:
    """Test the General Price sensor."""
    await setup_integration(hass, general_channel_config_entry)
    expect(len(hass.states.async_all())).to_equal(6)
    price = hass.states.get("sensor.mock_title_general_price")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("0.09")
    attributes = price.attributes
    expect(attributes["duration"]).to_equal(30)
    expect(attributes["date"]).to_equal("2021-09-21")
    expect(attributes["per_kwh"]).to_equal(0.09)
    expect(attributes["nem_date"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(attributes["spot_per_kwh"]).to_equal(0.01)
    expect(attributes["start_time"]).to_equal("2021-09-21T08:00:00+10:00")
    expect(attributes["end_time"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(attributes["renewables"]).to_equal(51)
    expect(attributes["estimate"]).to_be(True)
    expect(attributes["spike_status"]).to_equal("none")
    expect(attributes["channel_type"]).to_equal("general")
    expect(attributes["attribution"]).to_equal("Data provided by Amber Electric")
    expect(attributes.get("range_min")).to_be(None)
    expect(attributes.get("range_max")).to_be(None)


@test
async def general_price_sensor_with_range(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_config_entry: MockConfigEntry = Depends(
        general_channel_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_channel_with_range),
) -> None:
    """Test the General Price sensor with a range."""
    await setup_integration(hass, general_channel_config_entry)
    expect(len(hass.states.async_all())).to_equal(6)
    price = hass.states.get("sensor.mock_title_general_price")
    expect(price).to_be_truthy()
    attributes = price.attributes
    expect(attributes.get("range_min")).to_equal(0.07)
    expect(attributes.get("range_max")).to_equal(0.09)


@test
async def general_and_controlled_load_price_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_and_controlled_load_config_entry: MockConfigEntry = Depends(
        general_channel_and_controlled_load_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_and_controlled_load),
) -> None:
    """Test the Controlled Price sensor."""
    await setup_integration(hass, general_channel_and_controlled_load_config_entry)
    expect(len(hass.states.async_all())).to_equal(9)
    price = hass.states.get("sensor.mock_title_controlled_load_price")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("0.04")
    attributes = price.attributes
    expect(attributes["duration"]).to_equal(30)
    expect(attributes["date"]).to_equal("2021-09-21")
    expect(attributes["per_kwh"]).to_equal(0.04)
    expect(attributes["nem_date"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(attributes["spot_per_kwh"]).to_equal(0.01)
    expect(attributes["start_time"]).to_equal("2021-09-21T08:00:00+10:00")
    expect(attributes["end_time"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(attributes["renewables"]).to_equal(51)
    expect(attributes["estimate"]).to_be(True)
    expect(attributes["spike_status"]).to_equal("none")
    expect(attributes["channel_type"]).to_equal("controlledLoad")
    expect(attributes["attribution"]).to_equal("Data provided by Amber Electric")


@test
async def general_and_feed_in_price_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_and_feed_in_config_entry: MockConfigEntry = Depends(
        general_channel_and_feed_in_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_and_feed_in),
) -> None:
    """Test the Feed In sensor."""
    await setup_integration(hass, general_channel_and_feed_in_config_entry)
    expect(len(hass.states.async_all())).to_equal(9)
    price = hass.states.get("sensor.mock_title_feed_in_price")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("-0.01")
    attributes = price.attributes
    expect(attributes["duration"]).to_equal(30)
    expect(attributes["date"]).to_equal("2021-09-21")
    expect(attributes["per_kwh"]).to_equal(-0.01)
    expect(attributes["nem_date"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(attributes["spot_per_kwh"]).to_equal(0.01)
    expect(attributes["start_time"]).to_equal("2021-09-21T08:00:00+10:00")
    expect(attributes["end_time"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(attributes["renewables"]).to_equal(51)
    expect(attributes["estimate"]).to_be(True)
    expect(attributes["spike_status"]).to_equal("none")
    expect(attributes["channel_type"]).to_equal("feedIn")
    expect(attributes["attribution"]).to_equal("Data provided by Amber Electric")


@test
async def general_forecast_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_config_entry: MockConfigEntry = Depends(
        general_channel_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_channel),
) -> None:
    """Test the General Forecast sensor."""
    await setup_integration(hass, general_channel_config_entry)
    expect(len(hass.states.async_all())).to_equal(6)
    price = hass.states.get("sensor.mock_title_general_forecast")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("0.09")
    attributes = price.attributes
    expect(attributes["channel_type"]).to_equal("general")
    expect(attributes["attribution"]).to_equal("Data provided by Amber Electric")

    first_forecast = attributes["forecasts"][0]
    expect(first_forecast["duration"]).to_equal(30)
    expect(first_forecast["date"]).to_equal("2021-09-21")
    expect(first_forecast["per_kwh"]).to_equal(0.09)
    expect(first_forecast["nem_date"]).to_equal("2021-09-21T09:00:00+10:00")
    expect(first_forecast["spot_per_kwh"]).to_equal(0.01)
    expect(first_forecast["start_time"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(first_forecast["end_time"]).to_equal("2021-09-21T09:00:00+10:00")
    expect(first_forecast["renewables"]).to_equal(50)
    expect(first_forecast["spike_status"]).to_equal("none")
    expect(first_forecast["descriptor"]).to_equal("very_low")

    expect(first_forecast.get("range_min")).to_be(None)
    expect(first_forecast.get("range_max")).to_be(None)


@test
async def general_forecast_sensor_with_range(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_config_entry: MockConfigEntry = Depends(
        general_channel_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_channel_with_range),
) -> None:
    """Test the General Forecast sensor with a range."""
    await setup_integration(hass, general_channel_config_entry)
    expect(len(hass.states.async_all())).to_equal(6)
    price = hass.states.get("sensor.mock_title_general_forecast")
    expect(price).to_be_truthy()
    attributes = price.attributes
    first_forecast = attributes["forecasts"][0]
    expect(first_forecast.get("range_min")).to_equal(0.07)
    expect(first_forecast.get("range_max")).to_equal(0.09)


@test
async def controlled_load_forecast_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_and_controlled_load_config_entry: MockConfigEntry = Depends(
        general_channel_and_controlled_load_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_and_controlled_load),
) -> None:
    """Test the Controlled Load Forecast sensor."""
    await setup_integration(hass, general_channel_and_controlled_load_config_entry)
    expect(len(hass.states.async_all())).to_equal(9)
    price = hass.states.get("sensor.mock_title_controlled_load_forecast")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("0.04")
    attributes = price.attributes
    expect(attributes["channel_type"]).to_equal("controlledLoad")
    expect(attributes["attribution"]).to_equal("Data provided by Amber Electric")

    first_forecast = attributes["forecasts"][0]
    expect(first_forecast["duration"]).to_equal(30)
    expect(first_forecast["date"]).to_equal("2021-09-21")
    expect(first_forecast["per_kwh"]).to_equal(0.04)
    expect(first_forecast["nem_date"]).to_equal("2021-09-21T09:00:00+10:00")
    expect(first_forecast["spot_per_kwh"]).to_equal(0.01)
    expect(first_forecast["start_time"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(first_forecast["end_time"]).to_equal("2021-09-21T09:00:00+10:00")
    expect(first_forecast["renewables"]).to_equal(50)
    expect(first_forecast["spike_status"]).to_equal("none")
    expect(first_forecast["descriptor"]).to_equal("very_low")


@test
async def feed_in_forecast_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_and_feed_in_config_entry: MockConfigEntry = Depends(
        general_channel_and_feed_in_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_and_feed_in),
) -> None:
    """Test the Feed In Forecast sensor."""
    await setup_integration(hass, general_channel_and_feed_in_config_entry)
    expect(len(hass.states.async_all())).to_equal(9)
    price = hass.states.get("sensor.mock_title_feed_in_forecast")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("-0.01")
    attributes = price.attributes
    expect(attributes["channel_type"]).to_equal("feedIn")
    expect(attributes["attribution"]).to_equal("Data provided by Amber Electric")

    first_forecast = attributes["forecasts"][0]
    expect(first_forecast["duration"]).to_equal(30)
    expect(first_forecast["date"]).to_equal("2021-09-21")
    expect(first_forecast["per_kwh"]).to_equal(-0.01)
    expect(first_forecast["nem_date"]).to_equal("2021-09-21T09:00:00+10:00")
    expect(first_forecast["spot_per_kwh"]).to_equal(0.01)
    expect(first_forecast["start_time"]).to_equal("2021-09-21T08:30:00+10:00")
    expect(first_forecast["end_time"]).to_equal("2021-09-21T09:00:00+10:00")
    expect(first_forecast["renewables"]).to_equal(50)
    expect(first_forecast["spike_status"]).to_equal("none")
    expect(first_forecast["descriptor"]).to_equal("very_low")


@test
async def renewable_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_config_entry: MockConfigEntry = Depends(
        general_channel_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_channel),
) -> None:
    """Testing the creation of the Amber renewables sensor."""
    await setup_integration(hass, general_channel_config_entry)

    expect(len(hass.states.async_all())).to_equal(6)
    sensor = hass.states.get("sensor.mock_title_renewables")
    expect(sensor).to_be_truthy()
    expect(sensor.state).to_equal("51")


@test
async def general_price_descriptor_descriptor_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_config_entry: MockConfigEntry = Depends(
        general_channel_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_channel),
) -> None:
    """Test the General Price Descriptor sensor."""
    await setup_integration(hass, general_channel_config_entry)
    expect(len(hass.states.async_all())).to_equal(6)
    price = hass.states.get("sensor.mock_title_general_price_descriptor")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("extremely_low")


@test
async def general_and_controlled_load_price_descriptor_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_and_controlled_load_config_entry: MockConfigEntry = Depends(
        general_channel_and_controlled_load_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_and_controlled_load),
) -> None:
    """Test the Controlled Price Descriptor sensor."""
    await setup_integration(hass, general_channel_and_controlled_load_config_entry)

    expect(len(hass.states.async_all())).to_equal(9)
    price = hass.states.get("sensor.mock_title_controlled_load_price_descriptor")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("extremely_low")


@test
async def general_and_feed_in_price_descriptor_sensor(
    hass: HomeAssistant = Depends(hass_fx),
    general_channel_and_feed_in_config_entry: MockConfigEntry = Depends(
        general_channel_and_feed_in_config_entry
    ),
    _mock: AsyncMock = Depends(mock_amber_client_general_and_feed_in),
) -> None:
    """Test the Feed In Price Descriptor sensor."""
    await setup_integration(hass, general_channel_and_feed_in_config_entry)

    expect(len(hass.states.async_all())).to_equal(9)
    price = hass.states.get("sensor.mock_title_feed_in_price_descriptor")
    expect(price).to_be_truthy()
    expect(price.state).to_equal("extremely_low")
