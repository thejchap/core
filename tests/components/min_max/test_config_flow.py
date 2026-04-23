"""Test the Min/Max config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.min_max.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test.cases(test.case("sensor", "sensor"))
async def config_flow(
    platform: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""
    input_sensors = ["sensor.input_one", "sensor.input_two"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.min_max.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "My min_max", "entity_ids": input_sensors, "type": "max"},
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My min_max")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "entity_ids": input_sensors,
            "name": "My min_max",
            "round_digits": 2.0,
            "type": "max",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "entity_ids": input_sensors,
            "name": "My min_max",
            "round_digits": 2.0,
            "type": "max",
        }
    )
    expect(config_entry.title).to_equal("My min_max")


@test.cases(test.case("sensor", "sensor"))
async def options(
    platform: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    hass.states.async_set("sensor.input_one", "10")
    hass.states.async_set("sensor.input_two", "20")
    hass.states.async_set("sensor.input_three", "33.33")

    input_sensors1 = ["sensor.input_one", "sensor.input_two"]
    input_sensors2 = ["sensor.input_one", "sensor.input_two", "sensor.input_three"]

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_ids": input_sensors1,
            "name": "My min_max",
            "round_digits": 0,
            "type": "min",
        },
        title="My min_max",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema = result["data_schema"].schema
    expect(get_schema_suggested_value(schema, "entity_ids")).to_equal(input_sensors1)
    expect(get_schema_suggested_value(schema, "round_digits")).to_equal(0)
    expect(get_schema_suggested_value(schema, "type")).to_equal("min")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entity_ids": input_sensors2,
            "round_digits": 1,
            "type": "mean",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "entity_ids": input_sensors2,
            "name": "My min_max",
            "round_digits": 1,
            "type": "mean",
        }
    )
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "entity_ids": input_sensors2,
            "name": "My min_max",
            "round_digits": 1,
            "type": "mean",
        }
    )
    expect(config_entry.title).to_equal("My min_max")

    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(4)

    state = hass.states.get(f"{platform}.my_min_max")
    expect(state.state).to_equal("21.1")
