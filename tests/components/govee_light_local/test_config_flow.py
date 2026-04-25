"""Test Govee light local config flow."""

from errno import EADDRINUSE
from ipaddress import IPv4Address
from unittest.mock import AsyncMock, patch

from govee_local_api import GoveeDevice
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.govee_light_local.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_govee_api, mock_setup_entry
from .conftest import DEFAULT_CAPABILITIES

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _get_devices(api: AsyncMock) -> list[GoveeDevice]:
    return [
        GoveeDevice(
            controller=api,
            ip="192.168.1.100",
            fingerprint="asdawdqwdqwd1",
            sku="H615A",
            capabilities=DEFAULT_CAPABILITIES,
        )
    ]


@test
async def creating_entry_has_no_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    govee_api: AsyncMock = Depends(mock_govee_api),
) -> None:
    """Test setting up Govee with no devices."""

    govee_api.devices = []

    with patch(
        "homeassistant.components.govee_light_local.config_flow.DISCOVERY_TIMEOUT",
        0,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Confirmation form
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.ABORT)

        await hass.async_block_till_done()

        govee_api.start.assert_awaited_once()
        setup_entry.assert_not_called()


@test
async def creating_entry_has_with_devices(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    govee_api: AsyncMock = Depends(mock_govee_api),
) -> None:
    """Test setting up Govee with devices."""

    govee_api.devices = _get_devices(govee_api)

    # Mock duplicated IPs to ensure that only one GoveeController is started
    with patch(
        "homeassistant.components.network.async_get_enabled_source_ips",
        return_value=[IPv4Address("192.168.1.2"), IPv4Address("192.168.1.2")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # Confirmation form
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

        await hass.async_block_till_done()

    govee_api.start.assert_awaited_once()
    setup_entry.assert_awaited_once()


@test
async def creating_entry_errno(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    govee_api: AsyncMock = Depends(mock_govee_api),
) -> None:
    """Test setting up Govee with devices."""

    e = OSError()
    e.errno = EADDRINUSE
    govee_api.start.side_effect = e
    govee_api.devices = _get_devices(govee_api)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Confirmation form
    expect(result["type"]).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.ABORT)

    await hass.async_block_till_done()

    expect(govee_api.start.call_count).to_equal(1)
    setup_entry.assert_not_awaited()
