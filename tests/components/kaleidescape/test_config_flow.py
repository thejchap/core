"""Tests for Kaleidescape config flow."""

import dataclasses
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.kaleidescape.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_HOST, MOCK_SSDP_DISCOVERY_INFO
from ._fixtures import mock_config_entry, mock_device, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_config_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: MagicMock = Depends(mock_device),
) -> None:
    """Test user config flow success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: MOCK_HOST}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)


@test
async def user_config_flow_bad_connect_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: MagicMock = Depends(mock_device),
) -> None:
    """Test errors when connection error occurs."""
    mock_device.connect.side_effect = ConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: MOCK_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_config_flow_unsupported_device_errors(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: MagicMock = Depends(mock_device),
) -> None:
    """Test errors when connecting to unsupported device."""
    mock_device.is_server_only = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: MOCK_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "unsupported"})


@test
async def user_config_flow_device_exists_abort(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: MagicMock = Depends(mock_device),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test flow aborts when device already configured."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_HOST: MOCK_HOST}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_config_flow_success(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_device: MagicMock = Depends(mock_device),
) -> None:
    """Test ssdp config flow success."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_HOST]).to_equal(MOCK_HOST)


@test
async def ssdp_config_flow_bad_connect_aborts(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: MagicMock = Depends(mock_device),
) -> None:
    """Test abort when connection error occurs."""
    mock_device.connect.side_effect = ConnectionError

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_config_flow_unsupported_device_aborts(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_device: MagicMock = Depends(mock_device),
) -> None:
    """Test abort when connecting to unsupported device."""
    mock_device.is_server_only = True

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=discovery_info
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unsupported")
