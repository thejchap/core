"""Define tests for the israel rail config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.israel_rail import CONF_DESTINATION, CONF_START, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    VALID_CONFIG,
    mock_config_entry,
    mock_israelrail,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _israelrail: AsyncMock = Depends(mock_israelrail),
) -> None:
    """Test that the user step works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("באר יעקב אשקלון")
    expect(result["data"]).to_equal(
        {
            CONF_START: "באר יעקב",
            CONF_DESTINATION: "אשקלון",
        }
    )


@test
async def flow_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    israelrail: AsyncMock = Depends(mock_israelrail),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step fails."""
    israelrail.query.side_effect = Exception("error")
    failed_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=VALID_CONFIG,
    )

    expect(failed_result["errors"]).to_equal({"base": "unknown"})
    expect(failed_result["type"]).to_be(FlowResultType.FORM)

    israelrail.query.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        failed_result["flow_id"],
        VALID_CONFIG,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("באר יעקב אשקלון")
    expect(result["data"]).to_equal(
        {
            CONF_START: "באר יעקב",
            CONF_DESTINATION: "אשקלון",
        }
    )


@test
async def flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _israelrail: AsyncMock = Depends(mock_israelrail),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the user step fails when the entry is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result_aborted = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        VALID_CONFIG,
    )

    expect(result_aborted["type"]).to_be(FlowResultType.ABORT)
    expect(result_aborted["reason"]).to_equal("already_configured")
