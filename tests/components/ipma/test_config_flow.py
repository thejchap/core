"""Tests for IPMA config flow."""

from unittest.mock import patch

from pyipma import IPMAException
from tryke import Depends, expect, fixture, test

from homeassistant.components.ipma.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import init_integration, ipma_setup

from . import MockLocation

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _ipma_setup: None = Depends(ipma_setup),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    test_data = {
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
    }
    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            test_data,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("HomeTown")
    expect(result["data"]).to_equal(
        {
            CONF_LONGITUDE: 0,
            CONF_LATITUDE: 0,
        }
    )


@test
async def config_flow_failures(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test config flow with failures."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    test_data = {
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
    }
    with patch(
        "pyipma.location.Location.get",
        side_effect=IPMAException(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            test_data,
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "unknown"})
    with patch(
        "pyipma.location.Location.get",
        return_value=MockLocation(),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            test_data,
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("HomeTown")
    expect(result["data"]).to_equal(
        {
            CONF_LONGITUDE: 0,
            CONF_LATITUDE: 0,
        }
    )


@test
async def flow_entry_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test user input for config_entry that already exists.

    Test when the form should show when user puts existing location
    in the config gui. Then the form should show with error.
    """
    test_data = {
        CONF_NAME: "Home",
        CONF_LONGITUDE: 0,
        CONF_LATITUDE: 0,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=test_data
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
