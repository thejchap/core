"""Tests for the config_flow of the twinly component."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.twinkly.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_ID, CONF_MODEL, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import mock_config_entry, mock_setup_entry, mock_twinkly_client
from .const import TEST_MAC, TEST_MODEL, TEST_NAME

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _twinkly: AsyncMock = Depends(mock_twinkly_client),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Test the full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.0.123",
            CONF_ID: "00000000-0000-0000-0000-000000000000",
            CONF_NAME: TEST_NAME,
            CONF_MODEL: TEST_MODEL,
        }
    )
    expect(result["result"].unique_id).to_equal(TEST_MAC)


@test
async def exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    twinkly: AsyncMock = Depends(mock_twinkly_client),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Test the failure when raising exceptions."""
    twinkly.get_details.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({CONF_HOST: "cannot_connect"})

    twinkly.get_details.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.0.123"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _twinkly: AsyncMock = Depends(mock_twinkly_client),
    _setup_entry: None = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the device is already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.0.123"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _twinkly: AsyncMock = Depends(mock_twinkly_client),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Test DHCP discovery flow can confirm right away."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="Twinkly_XYZ",
            ip="1.2.3.4",
            macaddress="002d133baabb",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "1.2.3.4",
            CONF_ID: "00000000-0000-0000-0000-000000000000",
            CONF_NAME: TEST_NAME,
            CONF_MODEL: TEST_MODEL,
        }
    )
    expect(result["result"].unique_id).to_equal(TEST_MAC)


@test
async def dhcp_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _twinkly: AsyncMock = Depends(mock_twinkly_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test DHCP discovery flow aborts if entry already setup."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="Twinkly_XYZ",
            ip="1.2.3.4",
            macaddress="002d133baabb",
        ),
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.data[CONF_HOST]).to_equal("1.2.3.4")


@test
async def user_flow_works_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _twinkly: AsyncMock = Depends(mock_twinkly_client),
    _setup_entry: None = Depends(mock_setup_entry),
) -> None:
    """Test user flow can continue after discovery happened."""
    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="Twinkly_XYZ",
            ip="1.2.3.4",
            macaddress="002d133baabb",
        ),
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(len(hass.config_entries.flow.async_progress(DOMAIN))).to_equal(2)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "10.0.0.131"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    expect(bool(hass.config_entries.flow.async_progress(DOMAIN))).to_be(False)
