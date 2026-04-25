"""Test the lgthinq config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.lg_thinq.const import CONF_CONNECT_CLIENT_ID, DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_COUNTRY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_config_thinq_api,
    mock_invalid_thinq_api,
    mock_setup_entry,
    mock_uuid,
)
from .const import MOCK_CONNECT_CLIENT_ID, MOCK_COUNTRY, MOCK_PAT

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_DISCOVERY = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="LG_Smart_Dryer2_open",
    macaddress=dr.format_mac("34:E6:E6:11:22:33").replace(":", ""),
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    thinq_api: AsyncMock = Depends(mock_config_thinq_api),
    _uuid: AsyncMock = Depends(mock_uuid),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that an thinq entry is normally created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: MOCK_PAT, CONF_COUNTRY: MOCK_COUNTRY},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_ACCESS_TOKEN: MOCK_PAT,
            CONF_COUNTRY: MOCK_COUNTRY,
            CONF_CONNECT_CLIENT_ID: MOCK_CONNECT_CLIENT_ID,
        }
    )

    thinq_api.async_get_device_list.assert_called_once()


@test
async def config_flow_invalid_pat(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    invalid_api: AsyncMock = Depends(mock_invalid_thinq_api),
) -> None:
    """Test that an thinq flow should be aborted with an invalid PAT."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_ACCESS_TOKEN: MOCK_PAT, CONF_COUNTRY: MOCK_COUNTRY},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(True)
    invalid_api.async_get_device_list.assert_called_once()


@test
async def config_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _thinq_api: AsyncMock = Depends(mock_config_thinq_api),
) -> None:
    """Test that thinq flow should be aborted when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_ACCESS_TOKEN: MOCK_PAT, CONF_COUNTRY: MOCK_COUNTRY},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    thinq_api: AsyncMock = Depends(mock_config_thinq_api),
    _uuid: AsyncMock = Depends(mock_uuid),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that a thinq entry is normally created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ACCESS_TOKEN: MOCK_PAT, CONF_COUNTRY: MOCK_COUNTRY},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_ACCESS_TOKEN: MOCK_PAT,
            CONF_COUNTRY: MOCK_COUNTRY,
            CONF_CONNECT_CLIENT_ID: MOCK_CONNECT_CLIENT_ID,
        }
    )

    thinq_api.async_get_device_list.assert_called_once()


@test
async def dhcp_config_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _thinq_api: AsyncMock = Depends(mock_config_thinq_api),
) -> None:
    """Test that thinq flow should be aborted when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
