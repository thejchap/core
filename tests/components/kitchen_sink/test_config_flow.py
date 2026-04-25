"""Test the Everything but the Kitchen Sink config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.kitchen_sink import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component

from ._fixtures import infrared_only, no_platforms

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

ENTITY_IR_TRANSMITTER = "infrared.ir_blaster_infrared_transmitter"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def import_test(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we can import a config entry."""
    with patch("homeassistant.components.kitchen_sink.async_setup_entry"):
        await setup.async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.data).to_equal({})


@test
async def import_once(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we don't create multiple config entries."""
    with patch(
        "homeassistant.components.kitchen_sink.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={},
        )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Kitchen Sink")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal({})
    mock_setup_entry.assert_called_once()

    with patch(
        "homeassistant.components.kitchen_sink.async_setup_entry"
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={},
        )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")
    mock_setup_entry.assert_not_called()


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reauth works."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["handler"]).to_equal(DOMAIN)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(flows[0]["flow_id"], {})
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _no_platforms: None = Depends(no_platforms),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(
        True
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("options_1")

    section_marker, section_schema = list(result["data_schema"].schema.items())[0]
    expect(section_marker).to_equal("section_1")
    section_schema_markers = list(section_schema.schema.schema)
    expect(len(section_schema_markers)).to_equal(2)
    expect(section_schema_markers[0]).to_equal("bool")
    expect(section_schema_markers[0].description).to_be(None)
    expect(section_schema_markers[1]).to_equal("int")
    expect(section_schema_markers[1].description).to_equal({"suggested_value": 10})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"section_1": {"bool": True, "int": 15}},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({"section_1": {"bool": True, "int": 15}})

    await hass.async_block_till_done()


@test
async def subentry_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _no_platforms: None = Depends(no_platforms),
) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(
        True
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "entity"),
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("add_sensor")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={"name": "Sensor 1", "state": 15},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    subentry_id = list(config_entry.subentries)[0]
    expect(config_entry.subentries).to_equal(
        {
            subentry_id: config_entries.ConfigSubentry(
                data={"state": 15},
                subentry_id=subentry_id,
                subentry_type="entity",
                title="Sensor 1",
                unique_id=None,
            )
        }
    )

    await hass.async_block_till_done()


@test
async def subentry_reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _no_platforms: None = Depends(no_platforms),
) -> None:
    """Test config flow options."""
    subentry_id = "mock_id"
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={"state": 15},
                subentry_id="mock_id",
                subentry_type="entity",
                title="Sensor 1",
                unique_id=None,
            )
        ],
    )
    config_entry.add_to_hass(hass)

    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(
        True
    )
    await hass.async_block_till_done()

    result = await config_entry.start_subentry_reconfigure_flow(hass, subentry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_sensor")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={"name": "Renamed sensor 1", "state": 5},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")

    expect(config_entry.subentries).to_equal(
        {
            subentry_id: config_entries.ConfigSubentry(
                data={"state": 5},
                subentry_id=subentry_id,
                subentry_type="entity",
                title="Renamed sensor 1",
                unique_id=None,
            )
        }
    )

    await hass.async_block_till_done()


@test
async def infrared_fan_subentry_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _infrared_only: None = Depends(infrared_only),
) -> None:
    """Test infrared fan subentry flow creates an entry."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "infrared_fan"),
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        user_input={
            "name": "Living Room Fan",
            "infrared_entity_id": ENTITY_IR_TRANSMITTER,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    subentry_id = next(
        sid
        for sid, s in config_entry.subentries.items()
        if s.subentry_type == "infrared_fan"
    )
    expect(config_entry.subentries[subentry_id]).to_equal(
        config_entries.ConfigSubentry(
            data={"infrared_entity_id": ENTITY_IR_TRANSMITTER},
            subentry_id=subentry_id,
            subentry_type="infrared_fan",
            title="Living Room Fan",
            unique_id=None,
        )
    )


@test
async def infrared_fan_subentry_flow_no_emitters(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _no_platforms: None = Depends(no_platforms),
) -> None:
    """Test infrared fan subentry flow aborts when no emitters are available."""
    config_entry = MockConfigEntry(domain=DOMAIN)
    config_entry.add_to_hass(hass)

    expect(bool(await hass.config_entries.async_setup(config_entry.entry_id))).to_be(
        True
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (config_entry.entry_id, "infrared_fan"),
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_emitters")
