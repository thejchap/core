"""Test the Advantage Air config flow."""

from unittest.mock import AsyncMock, patch

from advantage_air import ApiError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.advantage_air.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import TEST_SYSTEM_DATA, USER_INPUT

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that form shows up."""

    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result1["type"]).to_be(FlowResultType.FORM)
    expect(result1["step_id"]).to_equal("user")
    expect(result1["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.advantage_air.config_flow.advantage_air.async_get",
            new=AsyncMock(return_value=TEST_SYSTEM_DATA),
        ) as mock_get,
        patch(
            "homeassistant.components.advantage_air.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()
        mock_setup_entry.assert_called_once()
        mock_get.assert_called_once()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("testname")
    expect(result2["data"]).to_equal(USER_INPUT)

    # Test duplicate config flow.
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.advantage_air.config_flow.advantage_air.async_get",
        new=AsyncMock(return_value=TEST_SYSTEM_DATA),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            USER_INPUT,
        )
    expect(result4["type"]).to_be(FlowResultType.ABORT)


@test
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "homeassistant.components.advantage_air.config_flow.advantage_air.async_get",
        new=AsyncMock(side_effect=ApiError),
    ) as mock_get:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        mock_get.assert_called_once()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["step_id"]).to_equal("user")
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
