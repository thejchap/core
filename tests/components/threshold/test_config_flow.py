"""Test the Threshold config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.threshold.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow."""
    input_sensor = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.threshold.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "entity_id": input_sensor,
                "lower": -2,
                "upper": 0.0,
                "name": "My threshold sensor",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My threshold sensor")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold sensor",
            "upper": 0.0,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold sensor",
            "upper": 0.0,
        }
    )
    expect(config_entry.title).to_equal("My threshold sensor")


@test.cases(test.case("need_lower_upper", extra_input_data={}, error="need_lower_upper"))
async def fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    extra_input_data: dict[str, object],
    error: str,
) -> None:
    """Test not providing lower or upper limit fails."""
    input_sensor = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "entity_id": input_sensor,
            "name": "My threshold sensor",
            **extra_input_data,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    input_sensor = "sensor.input"
    hass.states.async_set(input_sensor, "10")

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold",
            "upper": None,
        },
        title="My threshold",
    )
    config_entry.add_to_hass(hass)
    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(
        True
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema = result["data_schema"].schema
    expect(get_schema_suggested_value(schema, "hysteresis")).to_equal(0.0)
    expect(get_schema_suggested_value(schema, "lower")).to_equal(-2.0)
    expect(get_schema_suggested_value(schema, "upper")).to_be(None)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "upper": 20.0,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expected_options = {
        "entity_id": input_sensor,
        "hysteresis": 0.0,
        "lower": None,
        "name": "My threshold",
        "upper": 20.0,
    }
    expect(result["data"]).to_equal(expected_options)
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(expected_options)
    expect(config_entry.title).to_equal("My threshold")

    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(2)

    state = hass.states.get("binary_sensor.my_threshold")
    expect(state.state).to_equal("off")
    expect(state.attributes["type"]).to_equal("upper")


@test.skip("uses snapshot and hass_ws_client")
async def config_flow_preview_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow preview."""


@test.skip("uses snapshot and hass_ws_client")
async def options_flow_preview(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the options flow preview."""


@test.skip("uses hass_ws_client")
async def options_flow_sensor_preview_config_entry_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test option flow preview where config entry is removed."""
