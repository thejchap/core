"""Tests for the Zamg config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test
from zamg.exceptions import ZamgApiError

from homeassistant.components.zamg.const import CONF_STATION_ID, DOMAIN, LOGGER
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import TEST_STATION_ID, mock_setup_entry, mock_zamg

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _zamg: MagicMock = Depends(mock_zamg),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    LOGGER.debug(result)
    expect(result.get("data_schema") != "").to_be(True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_STATION_ID: TEST_STATION_ID},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_STATION_ID]).to_equal(TEST_STATION_ID)
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal(TEST_STATION_ID)


@test
async def error_closest_station(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    zamg: MagicMock = Depends(mock_zamg),
) -> None:
    """Test with error of reading from Zamg."""
    zamg.closest_station.side_effect = ZamgApiError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def error_update(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    zamg: MagicMock = Depends(mock_zamg),
) -> None:
    """Test with error of reading from Zamg."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    LOGGER.debug(result)
    expect(result.get("data_schema") != "").to_be(True)
    zamg.update.side_effect = ZamgApiError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_STATION_ID: TEST_STATION_ID},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def user_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _zamg: MagicMock = Depends(mock_zamg),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_STATION_ID: TEST_STATION_ID},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_STATION_ID]).to_equal(TEST_STATION_ID)
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal(TEST_STATION_ID)
    # Try to add another instance.
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_STATION_ID: TEST_STATION_ID},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
