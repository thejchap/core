"""Tests for the Arcam FMJ config flow module."""

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

from arcam.fmj.client import ConnectionFailed
from tryke import Depends, expect, fixture, test

from homeassistant.components.arcam_fmj.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import (
    ATTR_UPNP_DEVICE_TYPE,
    ATTR_UPNP_FRIENDLY_NAME,
    ATTR_UPNP_MANUFACTURER,
    ATTR_UPNP_MODEL_NAME,
    ATTR_UPNP_MODEL_NUMBER,
    ATTR_UPNP_SERIAL,
    ATTR_UPNP_UDN,
    SsdpServiceInfo,
)

from .conftest import (
    MOCK_CONFIG_ENTRY,
    MOCK_HOST,
    MOCK_NAME,
    MOCK_PORT,
    MOCK_UDN,
    MOCK_UUID,
)

from tests.common import MockConfigEntry
from tests.components.arcam_fmj._fixtures import (
    dummy_client,
    mock_config_entry,
    mock_setup_entry,
)
from tests.hass_fixtures import aioclient_mock, hass, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


MOCK_UPNP_DEVICE = f"""
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <device>
    <UDN>{MOCK_UDN}</UDN>
  </device>
</root>
"""

MOCK_UPNP_LOCATION = f"http://{MOCK_HOST}:8080/dd.xml"

MOCK_DISCOVER = SsdpServiceInfo(
    ssdp_usn="mock_usn",
    ssdp_st="mock_st",
    ssdp_location=f"http://{MOCK_HOST}:8080/dd.xml",
    upnp={
        ATTR_UPNP_MANUFACTURER: "ARCAM",
        ATTR_UPNP_MODEL_NAME: " ",
        ATTR_UPNP_MODEL_NUMBER: "AVR450, AVR750",
        ATTR_UPNP_FRIENDLY_NAME: f"Arcam media client {MOCK_UUID}",
        ATTR_UPNP_SERIAL: "12343",
        ATTR_UPNP_UDN: MOCK_UDN,
        ATTR_UPNP_DEVICE_TYPE: "urn:schemas-upnp-org:device:MediaRenderer:1",
    },
)


@test
async def ssdp(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a ssdp import flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"Arcam FMJ ({MOCK_HOST})")
    expect(result["data"]).to_equal(MOCK_CONFIG_ENTRY)


@test
async def ssdp_abort(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a ssdp import flow aborts when configured."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG_ENTRY, title=MOCK_NAME, unique_id=MOCK_UUID
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_unable_to_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a ssdp import flow that can't connect."""
    dummy_client.start.side_effect = AsyncMock(side_effect=ConnectionFailed)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_invalid_id(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a ssdp with invalid UDN."""
    discover = replace(
        MOCK_DISCOVER, upnp=MOCK_DISCOVER.upnp | {ATTR_UPNP_UDN: "invalid"}
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=discover,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def ssdp_update(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test a ssdp update flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "old_host", CONF_PORT: MOCK_PORT},
        title=MOCK_NAME,
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=MOCK_DISCOVER,
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")

    expect(entry.data[CONF_HOST]).to_equal(MOCK_HOST)


@test
async def user(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test a manual user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=None,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    user_input = {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }

    aioclient_mock.get(MOCK_UPNP_LOCATION, text=MOCK_UPNP_DEVICE)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"Arcam FMJ ({MOCK_HOST})")
    expect(result["data"]).to_equal(MOCK_CONFIG_ENTRY)
    expect(result["result"].unique_id).to_equal(MOCK_UUID)


@test
async def invalid_ssdp(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test a config flow where ssdp fails."""
    user_input = {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }

    aioclient_mock.get(MOCK_UPNP_LOCATION, text="")
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"Arcam FMJ ({MOCK_HOST})")
    expect(result["data"]).to_equal(MOCK_CONFIG_ENTRY)
    expect(result["result"].unique_id is None).to_be(True)


@test
async def user_wrong(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _dummy_client: MagicMock = Depends(dummy_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test a manual user configuration flow with no ssdp response."""
    user_input = {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
    }

    aioclient_mock.get(MOCK_UPNP_LOCATION, status=404)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=user_input,
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal(f"Arcam FMJ ({MOCK_HOST})")
    expect(result["result"].unique_id is None).to_be(True)
