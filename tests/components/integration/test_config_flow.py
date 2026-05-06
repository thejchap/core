"""Test the Integration - Riemann sum integral config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.integration.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import selector

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(test.case("sensor", platform="sensor"))
async def config_flow(
    platform: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.integration.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "method": "left",
                "name": "My integration",
                "round": 1,
                "source": input_sensor_entity_id,
                "unit_time": "min",
                "max_sub_interval": {"seconds": 0},
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My integration")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "method": "left",
            "name": "My integration",
            "round": 1.0,
            "source": "sensor.input",
            "unit_time": "min",
            "max_sub_interval": {"seconds": 0},
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "method": "left",
            "name": "My integration",
            "round": 1.0,
            "source": "sensor.input",
            "unit_time": "min",
            "max_sub_interval": {"seconds": 0},
        }
    )
    expect(config_entry.title).to_equal("My integration")


@test.cases(test.case("sensor", platform="sensor"))
async def options(
    platform: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "left",
            "name": "My integration",
            "round": 1.0,
            "source": "sensor.input",
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        },
        title="My integration",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.input", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.invalid", 10, {"unit_of_measurement": "cat"})

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema = result["data_schema"].schema
    expect(get_schema_suggested_value(schema, "round")).to_equal(1.0)

    source = schema["source"]
    expect(isinstance(source, selector.EntitySelector)).to_be(True)
    expect(source.config["include_entities"]).to_equal(
        [
            "sensor.input",
            "sensor.valid",
        ]
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "method": "right",
            "round": 2.0,
            "source": "sensor.input",
            "max_sub_interval": {"minutes": 1},
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "method": "right",
            "name": "My integration",
            "round": 2.0,
            "source": "sensor.input",
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        }
    )
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "method": "right",
            "name": "My integration",
            "round": 2.0,
            "source": "sensor.input",
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        }
    )
    expect(config_entry.title).to_equal("My integration")

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    expect(len(hass.states.async_all())).to_equal(4)

    # Check the state of the entity has changed as expected
    hass.states.async_set("sensor.input", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.input", 11, {"unit_of_measurement": "dog"})
    await hass.async_block_till_done()

    state = hass.states.get(f"{platform}.my_integration")
    expect(state.state != "unknown").to_be(True)
    expect(state.attributes["unit_of_measurement"]).to_equal("kdogmin")
