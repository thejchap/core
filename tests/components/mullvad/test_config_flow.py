"""Test the Mullvad config flow."""

from unittest.mock import patch

from mullvad_api import MullvadAPIError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries, setup
from homeassistant.components.mullvad.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form_user(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can setup by the user."""
    await setup.async_setup_component(hass, DOMAIN, {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be_falsy()

    with (
        patch(
            "homeassistant.components.mullvad.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.mullvad.config_flow.MullvadAPI"
        ) as mock_mullvad_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Mullvad VPN")
    expect(result2["data"]).to_equal({})
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)
    expect(len(mock_mullvad_api.mock_calls)).to_equal(1)


@test
async def form_user_only_once(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can setup by the user only once."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show an error when we have trouble connecting."""
    await setup.async_setup_component(hass, DOMAIN, {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.mullvad.config_flow.MullvadAPI",
        side_effect=MullvadAPIError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def unknown_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we show an error when an unknown error occurs."""
    await setup.async_setup_component(hass, DOMAIN, {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.mullvad.config_flow.MullvadAPI",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})
