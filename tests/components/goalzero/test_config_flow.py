"""Test Goal Zero Yeti config flow."""

from unittest.mock import patch

from goalzero import exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.goalzero.const import DEFAULT_NAME, DOMAIN, MANUFACTURER
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    CONF_DATA,
    CONF_DHCP_FLOW,
    MAC,
    create_entry,
    create_mocked_yeti,
    patch_config_flow_yeti,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _patch_setup():
    return patch("homeassistant.components.goalzero.async_setup_entry")


@test
async def flow_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow."""
    mocked_yeti = await create_mocked_yeti()
    with patch_config_flow_yeti(mocked_yeti), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(DEFAULT_NAME)
        expect(result["data"]).to_equal(CONF_DATA)
        expect(result["result"].unique_id).to_equal(MAC)


@test
async def flow_user_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with duplicate server."""
    create_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def flow_user_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_config_flow_yeti(await create_mocked_yeti()) as yetimock:
        yetimock.side_effect = exceptions.ConnectError
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("cannot_connect")


@test
async def flow_user_invalid_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with invalid server."""
    with patch_config_flow_yeti(await create_mocked_yeti()) as yetimock:
        yetimock.side_effect = exceptions.InvalidHost
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("invalid_host")


@test
async def flow_user_unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user initialized flow with unreachable server."""
    with patch_config_flow_yeti(await create_mocked_yeti()) as yetimock:
        yetimock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_DATA
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]["base"]).to_equal("unknown")


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we can process the discovery from dhcp."""
    mocked_yeti = await create_mocked_yeti()
    with patch_config_flow_yeti(mocked_yeti), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal(MANUFACTURER)
        expect(result["data"]).to_equal(CONF_DATA)
        expect(result["result"].unique_id).to_equal(MAC)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_discovery_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test failed setup from dhcp."""
    mocked_yeti = await create_mocked_yeti()
    with patch_config_flow_yeti(mocked_yeti) as yetimock:
        yetimock.side_effect = exceptions.ConnectError
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")

    with patch_config_flow_yeti(mocked_yeti) as yetimock:
        yetimock.side_effect = exceptions.InvalidHost
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("invalid_host")

    with patch_config_flow_yeti(mocked_yeti) as yetimock:
        yetimock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("unknown")
