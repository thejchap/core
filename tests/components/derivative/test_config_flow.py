"""Test the Derivative config flow."""

from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.derivative.const import DOMAIN
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import selector
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case("sensor", platform="sensor"),
)
async def config_flow(
    *,
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
        "homeassistant.components.derivative.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My derivative",
                "round": 1,
                "source": input_sensor_entity_id,
                "time_window": {"seconds": 0},
                "unit_time": "min",
                "max_sub_interval": {"minutes": 1},
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My derivative")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.input",
            "time_window": {"seconds": 0.0},
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1.0},
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.input",
            "time_window": {"seconds": 0.0},
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1.0},
        }
    )
    expect(config_entry.title).to_equal("My derivative")


@test.cases(
    test.case("sensor_k", platform="sensor", unit_prefix_entry="k", unit_prefix_used="k"),
    test.case(
        "sensor_micro_sign",
        platform="sensor",
        unit_prefix_entry="µ",
        unit_prefix_used="μ",
    ),
    test.case(
        "sensor_mu",
        platform="sensor",
        unit_prefix_entry="μ",
        unit_prefix_used="μ",
    ),
)
async def options(
    *,
    platform: str,
    unit_prefix_entry: str,
    unit_prefix_used: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring and migrated unit prefix."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.input",
            "time_window": {"seconds": 0.0},
            "unit_prefix": unit_prefix_entry,
            "unit_time": "min",
            "max_sub_interval": {"seconds": 30},
        },
        title="My derivative",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.input", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.invalid", 10, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema = result["data_schema"].schema
    expect(get_schema_suggested_value(schema, "round")).to_equal(1.0)
    expect(get_schema_suggested_value(schema, "time_window")).to_equal({"seconds": 0.0})
    expect(get_schema_suggested_value(schema, "unit_prefix")).to_equal(unit_prefix_used)
    expect(get_schema_suggested_value(schema, "unit_time")).to_equal("min")

    source = schema["source"]
    expect(isinstance(source, selector.EntitySelector)).to_be(True)
    expect(source.config["include_entities"]).to_equal(
        [
            "sensor.input",
            "sensor.valid",
        ]
    )

    state = hass.states.get(f"{platform}.my_derivative")
    expect(state.attributes["unit_of_measurement"]).to_equal(
        f"{unit_prefix_used}dog/min"
    )
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "source": "sensor.valid",
            "round": 2.0,
            "time_window": {"seconds": 10.0},
            "unit_time": "h",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "name": "My derivative",
            "round": 2.0,
            "source": "sensor.valid",
            "time_window": {"seconds": 10.0},
            "unit_time": "h",
        }
    )
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "name": "My derivative",
            "round": 2.0,
            "source": "sensor.valid",
            "time_window": {"seconds": 10.0},
            "unit_time": "h",
        }
    )
    expect(config_entry.title).to_equal("My derivative")

    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(4)

    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "cat"})
    hass.states.async_set("sensor.valid", 11, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()
    state = hass.states.get(f"{platform}.my_derivative")
    expect(state.attributes["unit_of_measurement"]).to_equal("cat/h")


@test
async def update_unit(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test behavior of changing the unit_time option."""
    source_id = "sensor.source"
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": source_id,
            "unit_time": "min",
            "time_window": {"seconds": 0.0},
        },
        title="My derivative",
    )
    derivative_id = "sensor.my_derivative"
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get(derivative_id)
    expect(state.state).to_equal(STATE_UNAVAILABLE)
    expect(state.attributes.get("unit_of_measurement")).to_be(None)

    time = dt_util.utcnow()
    with freeze_time(time) as freezer:
        hass.states.async_set(source_id, 5, {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        expect(state.state).to_equal("0.0")
        expect(state.attributes.get("unit_of_measurement")).to_equal("dogs/min")

        time += timedelta(minutes=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "7", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        expect(state.state).to_equal("2.0")
        expect(state.attributes.get("unit_of_measurement")).to_equal("dogs/min")

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "source": source_id,
                "round": 1.0,
                "unit_time": "s",
                "time_window": {"seconds": 0.0},
            },
        )
        await hass.async_block_till_done()

        state = hass.states.get(derivative_id)
        expect(state.state).to_equal("0.0")
        expect(state.attributes.get("unit_of_measurement")).to_equal("dogs/s")

        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "10", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        expect(state.state).to_equal("3.0")
        expect(state.attributes.get("unit_of_measurement")).to_equal("dogs/s")

        time += timedelta(seconds=1)
        freezer.move_to(time)
        hass.states.async_set(source_id, "20", {"unit_of_measurement": "dogs"})
        await hass.async_block_till_done()
        state = hass.states.get(derivative_id)
        expect(state.state).to_equal("10.0")
        expect(state.attributes.get("unit_of_measurement")).to_equal("dogs/s")
