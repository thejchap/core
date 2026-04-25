"""Test the Times of the Day config flow."""

from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.tod.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(test.case("sensor", platform="sensor"))
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    platform: str,
) -> None:
    """Test the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.tod.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "after_time": "10:00",
                "before_time": "18:00",
                "name": "My tod",
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My tod")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "after_time": "10:00",
            "before_time": "18:00",
            "name": "My tod",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "after_time": "10:00",
            "before_time": "18:00",
            "name": "My tod",
        }
    )
    expect(config_entry.title).to_equal("My tod")


@test.skip("Requires pytest-freezer tz_offset semantics not available in tryke")
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    with freeze_time("2022-03-16 17:37:00"):
        # Setup the config entry
        config_entry = MockConfigEntry(
            data={},
            domain=DOMAIN,
            options={
                "after_time": "10:00",
                "before_time": "18:05",
                "name": "My tod",
            },
            title="My tod",
        )
        config_entry.add_to_hass(hass)
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")
        schema = result["data_schema"].schema
        expect(get_schema_suggested_value(schema, "after_time")).to_equal("10:00")
        expect(get_schema_suggested_value(schema, "before_time")).to_equal("18:05")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "after_time": "10:00",
                "before_time": "17:05",
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal(
            {
                "after_time": "10:00",
                "before_time": "17:05",
                "name": "My tod",
            }
        )
        expect(config_entry.data).to_equal({})
        expect(config_entry.options).to_equal(
            {
                "after_time": "10:00",
                "before_time": "17:05",
                "name": "My tod",
            }
        )
        expect(config_entry.title).to_equal("My tod")

        # Check config entry is reloaded with new options
        await hass.async_block_till_done()

        # Check the entity was updated, no new entity was created
        expect(len(hass.states.async_all())).to_equal(1)

        # Check the state of the entity has changed as expected
        state = hass.states.get("binary_sensor.my_tod")
        expect(state.state).to_equal("off")
