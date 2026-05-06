"""Test AfterShip config flow."""

from unittest.mock import AsyncMock, patch

from pyaftership import AfterShipException
from tryke import Depends, expect, fixture, test

from homeassistant.components.aftership.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.aftership.config_flow.AfterShip",
        return_value=AsyncMock(),
    ) as mock_aftership:
        mock_aftership.return_value.trackings.return_value.list.return_value = {}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "mock-api-key",
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("AfterShip")
        expect(result["data"]).to_equal(
            {
                CONF_API_KEY: "mock-api-key",
            }
        )


@test
async def flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling invalid connection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch(
        "homeassistant.components.aftership.config_flow.AfterShip",
        return_value=AsyncMock(),
    ) as mock_aftership:
        mock_aftership.side_effect = AfterShipException
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "mock-api-key",
            },
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")

    with patch(
        "homeassistant.components.aftership.config_flow.AfterShip",
        return_value=AsyncMock(),
    ) as mock_aftership:
        mock_aftership.return_value.trackings.return_value.list.return_value = {}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_API_KEY: "mock-api-key",
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("AfterShip")
        expect(result["data"]).to_equal(
            {
                CONF_API_KEY: "mock-api-key",
            }
        )
