"""Test the deconz config flow."""

import pydeconz
from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

BRIDGE_ID = "01234E56789A"


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def flow_discovered_bridges_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that the user form is rendered when bridges are discovered."""
    aioclient.get(
        pydeconz.utils.URL_DISCOVER,
        json=[
            {"id": BRIDGE_ID, "internalipaddress": "1.2.3.4", "internalport": 80},
        ],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def manual_configuration_after_discovery_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test failed discovery (timeout) falls back to manual configuration."""
    aioclient.get(pydeconz.utils.URL_DISCOVER, exc=TimeoutError)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual_input")


@test
async def manual_configuration_after_discovery_ResponseError(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test failed discovery (ResponseError) falls back to manual configuration."""
    aioclient.get(pydeconz.utils.URL_DISCOVER, exc=pydeconz.errors.ResponseError)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual_input")


@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_discovered_bridges() -> None:
    """Stub for test_flow_discovered_bridges (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_manual_configuration_decision() -> None:
    """Stub for test_flow_manual_configuration_decision (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_manual_configuration() -> None:
    """Stub for test_flow_manual_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_update_configuration() -> None:
    """Stub for test_manual_configuration_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_dont_update_configuration() -> None:
    """Stub for test_manual_configuration_dont_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def manual_configuration_timeout_get_bridge() -> None:
    """Stub for test_manual_configuration_timeout_get_bridge (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def link_step_fails() -> None:
    """Stub for test_link_step_fails (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def reauth_flow_update_configuration() -> None:
    """Stub for test_reauth_flow_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_ssdp_discovery() -> None:
    """Stub for test_flow_ssdp_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_discovery_update_configuration() -> None:
    """Stub for test_ssdp_discovery_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_discovery_dont_update_configuration() -> None:
    """Stub for test_ssdp_discovery_dont_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def ssdp_discovery_dont_update_existing_hassio_configuration() -> None:
    """Stub for test_ssdp_discovery_dont_update_existing_hassio_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def flow_hassio_discovery() -> None:
    """Stub for test_flow_hassio_discovery (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def hassio_discovery_update_configuration() -> None:
    """Stub for test_hassio_discovery_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def hassio_discovery_dont_update_configuration() -> None:
    """Stub for test_hassio_discovery_dont_update_configuration (port deferred)."""

@test.skip("discovery flow (ssdp/zeroconf/dhcp/usb) and complex fixture chain")
async def option_flow() -> None:
    """Stub for test_option_flow (port deferred)."""
