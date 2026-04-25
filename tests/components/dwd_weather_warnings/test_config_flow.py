"""Tests for Deutscher Wetterdienst (DWD) Weather Warnings config flow."""

from typing import Final
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.dwd_weather_warnings.const import (
    CONF_REGION_DEVICE_TRACKER,
    CONF_REGION_IDENTIFIER,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, STATE_HOME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er

from ._fixtures import mock_dwdwfsapi, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)

DEMO_CONFIG_ENTRY_REGION: Final = {
    CONF_REGION_IDENTIFIER: "807111000",
}

DEMO_CONFIG_ENTRY_GPS: Final = {
    CONF_REGION_DEVICE_TRACKER: "device_tracker.test_gps",
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def create_entry_region(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    dwdwfsapi: MagicMock = Depends(mock_dwdwfsapi),
) -> None:
    """Test that the full config flow works for a region identifier."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)

    dwdwfsapi.__bool__.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_REGION
    )

    # Test for invalid region identifier.
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_identifier"})

    dwdwfsapi.__bool__.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_REGION
    )

    # Test for successfully created entry.
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("807111000")
    expect(result["data"]).to_equal(
        {
            CONF_REGION_IDENTIFIER: "807111000",
        }
    )


@test
async def create_entry_gps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    dwdwfsapi: MagicMock = Depends(mock_dwdwfsapi),
) -> None:
    """Test that the full config flow works for a device tracker."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)

    # Test for missing registry entry error.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "entity_not_found"})

    # Test for missing device tracker error.
    registry_entry = entity_registry.async_get_or_create(
        "device_tracker", DOMAIN, "uuid", suggested_object_id="test_gps"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "entity_not_found"})

    # Test for missing attribute error.
    hass.states.async_set(
        DEMO_CONFIG_ENTRY_GPS[CONF_REGION_DEVICE_TRACKER],
        STATE_HOME,
        {ATTR_LONGITUDE: "7.610263"},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "attribute_not_found"})

    # Test for invalid provided identifier.
    hass.states.async_set(
        DEMO_CONFIG_ENTRY_GPS[CONF_REGION_DEVICE_TRACKER],
        STATE_HOME,
        {ATTR_LATITUDE: "50.180454", ATTR_LONGITUDE: "7.610263"},
    )

    dwdwfsapi.__bool__.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_identifier"})

    # Test for successfully created entry.
    dwdwfsapi.__bool__.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test_gps")
    expect(result["data"]).to_equal(
        {
            CONF_REGION_DEVICE_TRACKER: registry_entry.id,
        }
    )


@test
async def config_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _dwdwfsapi: MagicMock = Depends(mock_dwdwfsapi),
) -> None:
    """Test aborting, if the warncell ID / name is already configured during the config."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=DEMO_CONFIG_ENTRY_REGION.copy(),
        unique_id=DEMO_CONFIG_ENTRY_REGION[CONF_REGION_IDENTIFIER],
    )
    entry.add_to_hass(hass)

    # Start configuration of duplicate entry.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_REGION
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def config_flow_with_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test error scenarios during the configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)

    # Test error for empty input data.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "no_identifier"})

    # Test error for setting both options during configuration.
    demo_input = DEMO_CONFIG_ENTRY_REGION.copy()
    demo_input.update(DEMO_CONFIG_ENTRY_GPS.copy())
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=demo_input,
    )

    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "ambiguous_identifier"})
