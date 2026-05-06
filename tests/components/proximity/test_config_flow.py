"""Test proximity config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.proximity.const import (
    CONF_IGNORED_ZONES,
    CONF_TOLERANCE,
    CONF_TRACKED_ENTITIES,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import config_zones

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _trigger_executor(_zones: None = Depends(config_zones)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(
    test.case(
        "minimal",
        user_input={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
        },
        expected_result={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
            CONF_IGNORED_ZONES: [],
            CONF_TOLERANCE: 1,
        },
    ),
    test.case(
        "with_ignored_zones_and_tolerance",
        user_input={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
            CONF_IGNORED_ZONES: ["zone.work"],
            CONF_TOLERANCE: 10,
        },
        expected_result={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
            CONF_IGNORED_ZONES: ["zone.work"],
            CONF_TOLERANCE: 10,
        },
    ),
)
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
    *,
    user_input: dict,
    expected_result: dict,
) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.proximity.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=user_input,
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"]).to_equal(expected_result)

        zone = hass.states.get(user_input[CONF_ZONE])
        expect(result["title"]).to_equal(zone.name)

        await hass.async_block_till_done()

    expect(mock_setup_entry.called).to_be(True)


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test options flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        title="home",
        data={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
            CONF_IGNORED_ZONES: ["zone.work"],
            CONF_TOLERANCE: 10,
        },
        unique_id=f"{DOMAIN}_home",
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.proximity.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        await hass.config_entries.async_setup(mock_config.entry_id)
        await hass.async_block_till_done()
        expect(mock_setup_entry.called).to_be(True)

        result = await hass.config_entries.options.async_init(mock_config.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_TRACKED_ENTITIES: ["device_tracker.test2"],
            CONF_IGNORED_ZONES: [],
            CONF_TOLERANCE: 1,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(mock_config.data).to_equal(
        {
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test2"],
            CONF_IGNORED_ZONES: [],
            CONF_TOLERANCE: 1,
        }
    )


@test
async def abort_duplicated_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test if we abort on duplicate user input data."""
    DATA = {
        CONF_ZONE: "zone.home",
        CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
        CONF_IGNORED_ZONES: ["zone.work"],
        CONF_TOLERANCE: 10,
    }
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        title="home",
        data=DATA,
        unique_id=f"{DOMAIN}_home",
    )
    mock_config.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    with patch(
        "homeassistant.components.proximity.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=DATA,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")

        await hass.async_block_till_done()


@test
async def avoid_duplicated_title(
    hass: HomeAssistant = Depends(hass_fixture),
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test if we avoid duplicate titles."""
    MockConfigEntry(
        domain=DOMAIN,
        title="home",
        data={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test1"],
            CONF_IGNORED_ZONES: ["zone.work"],
            CONF_TOLERANCE: 10,
        },
        unique_id=f"{DOMAIN}_home",
    ).add_to_hass(hass)

    MockConfigEntry(
        domain=DOMAIN,
        title="home 3",
        data={
            CONF_ZONE: "zone.home",
            CONF_TRACKED_ENTITIES: ["device_tracker.test2"],
            CONF_IGNORED_ZONES: ["zone.work"],
            CONF_TOLERANCE: 10,
        },
        unique_id=f"{DOMAIN}_home_3",
    ).add_to_hass(hass)

    with patch(
        "homeassistant.components.proximity.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_ZONE: "zone.home",
                CONF_TRACKED_ENTITIES: ["device_tracker.test3"],
                CONF_IGNORED_ZONES: [],
                CONF_TOLERANCE: 10,
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("home 2")

        await hass.async_block_till_done()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_ZONE: "zone.home",
                CONF_TRACKED_ENTITIES: ["device_tracker.test4"],
                CONF_IGNORED_ZONES: [],
                CONF_TOLERANCE: 10,
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("home 4")

        await hass.async_block_till_done()
