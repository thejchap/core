"""Test the nuki config flow."""

from __future__ import annotations

from unittest.mock import patch

from pynuki.bridge import InvalidCredentialsException
from requests.exceptions import RequestException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nuki.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from tests.hass_fixtures import hass as hass_fixture, mock_network

from .mock import DHCP_FORMATTED_MAC, HOST, MOCK_INFO, NAME, setup_nuki_integration


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch(
            "homeassistant.components.nuki.config_flow.NukiBridge.info",
            return_value=MOCK_INFO,
        ),
        patch(
            "homeassistant.components.nuki.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("BC614E")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 8080,
            CONF_TOKEN: "test-token",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def form_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        side_effect=InvalidCredentialsException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        side_effect=RequestException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def form_unknown_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def form_already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we get the form."""
    await setup_nuki_integration(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        return_value=MOCK_INFO,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("already_configured")


@test
async def dhcp_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that DHCP discovery for new bridge works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(hostname=NAME, ip=HOST, macaddress=DHCP_FORMATTED_MAC),
        context={"source": config_entries.SOURCE_DHCP},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

    with (
        patch(
            "homeassistant.components.nuki.config_flow.NukiBridge.info",
            return_value=MOCK_INFO,
        ),
        patch(
            "homeassistant.components.nuki.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            },
        )

        expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result2["title"]).to_equal("BC614E")
        expect(result2["data"]).to_equal(
            {
                CONF_HOST: "1.1.1.1",
                CONF_PORT: 8080,
                CONF_TOKEN: "test-token",
            }
        )

        await hass.async_block_till_done()
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def dhcp_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP doesn't setup already configured devices."""
    await setup_nuki_integration(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=DhcpServiceInfo(hostname=NAME, ip=HOST, macaddress=DHCP_FORMATTED_MAC),
        context={"source": config_entries.SOURCE_DHCP},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_success(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a reauthentication flow."""
    entry = await setup_nuki_integration(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with (
        patch(
            "homeassistant.components.nuki.config_flow.NukiBridge.info",
            return_value=MOCK_INFO,
        ),
        patch(
            "homeassistant.components.nuki.async_setup_entry",
            return_value=True,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TOKEN: "new-token"},
        )
        await hass.async_block_till_done()

        expect(result2["type"]).to_be(FlowResultType.ABORT)
        expect(result2["reason"]).to_equal("reauth_successful")
        expect(entry.data[CONF_TOKEN]).to_equal("new-token")


@test
async def reauth_invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a reauthentication flow with invalid auth."""
    entry = await setup_nuki_integration(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        side_effect=InvalidCredentialsException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TOKEN: "new-token"},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reauth_confirm")
        expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def reauth_cannot_connect(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a reauthentication flow with cannot connect."""
    entry = await setup_nuki_integration(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        side_effect=RequestException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TOKEN: "new-token"},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reauth_confirm")
        expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def reauth_unknown_exception(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test starting a reauthentication flow with an unknown exception."""
    entry = await setup_nuki_integration(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.nuki.config_flow.NukiBridge.info",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_TOKEN: "new-token"},
        )

        expect(result2["type"]).to_be(FlowResultType.FORM)
        expect(result2["step_id"]).to_equal("reauth_confirm")
        expect(result2["errors"]).to_equal({"base": "unknown"})
