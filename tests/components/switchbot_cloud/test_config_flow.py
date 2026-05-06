"""Test the SwitchBot via API config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.switchbot_cloud.config_flow import (
    SwitchBotAuthenticationError,
    SwitchBotConnectionError,
)
from homeassistant.components.switchbot_cloud.const import DOMAIN, ENTRY_TITLE
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


async def _fill_out_form_and_assert_entry_created(
    hass: HomeAssistant, flow_id: str, setup_entry: AsyncMock
) -> None:
    """Fill out the user form and assert a config entry is created."""
    with patch(
        "homeassistant.components.switchbot_cloud.config_flow.SwitchBotAPI.list_devices",
        return_value=[],
    ):
        result_configure = await hass.config_entries.flow.async_configure(
            flow_id,
            {
                CONF_API_TOKEN: "test-token",
                CONF_API_KEY: "test-secret-key",
            },
        )
        await hass.async_block_till_done()

        expect(result_configure["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result_configure["title"]).to_equal(ENTRY_TITLE)
        expect(result_configure["data"]).to_equal(
            {
                CONF_API_TOKEN: "test-token",
                CONF_API_KEY: "test-secret-key",
            }
        )
        setup_entry.assert_called_once()


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result_init["type"]).to_be(FlowResultType.FORM)
    expect(bool(result_init["errors"])).to_be(False)

    await _fill_out_form_and_assert_entry_created(
        hass, result_init["flow_id"], setup_entry
    )


@test.cases(
    test.case("invalid_auth", error=SwitchBotAuthenticationError, message="invalid_auth"),
    test.case("cannot_connect", error=SwitchBotConnectionError, message="cannot_connect"),
    test.case("unknown", error=Exception, message="unknown"),
)
async def form_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    error: type[Exception],
    message: str,
) -> None:
    """Test we handle error cases."""
    result_init = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.switchbot_cloud.config_flow.SwitchBotAPI.list_devices",
        side_effect=error,
    ):
        result_configure = await hass.config_entries.flow.async_configure(
            result_init["flow_id"],
            {
                CONF_API_TOKEN: "test-token",
                CONF_API_KEY: "test-secret-key",
            },
        )

        expect(result_configure["type"]).to_be(FlowResultType.FORM)
        expect(result_configure["errors"]).to_equal({"base": message})
        await hass.async_block_till_done()

    await _fill_out_form_and_assert_entry_created(
        hass, result_init["flow_id"], setup_entry
    )
