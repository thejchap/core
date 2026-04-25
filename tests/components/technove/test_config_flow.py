"""Tests for the TechnoVE config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from technove import TechnoVEConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.technove.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_onboarding,
    mock_setup_entry,
    mock_technove,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
    )

    expect(result.get("title")).to_equal("TechnoVE Station")
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("AA:AA:AA:AA:AA:BB")


@test
async def user_device_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test we abort the config flow if TechnoVE station is already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "192.168.1.123"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test we show user form on TechnoVE connection error."""
    technove.update.side_effect = TechnoVEConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "example.com"},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def full_user_flow_with_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test the full manual user flow from start to finish with some errors in the middle."""
    technove.update.side_effect = TechnoVEConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result.get("step_id")).to_equal("user")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})

    technove.update.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
    )

    expect(result.get("title")).to_equal("TechnoVE Station")
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect("data" in result).to_be(True)
    expect(result["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("AA:AA:AA:AA:AA:BB")


@test
async def full_zeroconf_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "AA:AA:AA:AA:AA:BB"},
            type="mock_type",
        ),
    )

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    expect(result.get("description_placeholders")).to_equal({CONF_NAME: "TechnoVE Station"})
    expect(result.get("step_id")).to_equal("zeroconf_confirm")
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result2.get("title")).to_equal("TechnoVE Station")
    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect("data" in result2).to_be(True)
    expect(result2["data"][CONF_HOST]).to_equal("192.168.1.123")
    expect("result" in result2).to_be(True)
    expect(result2["result"].unique_id).to_equal("AA:AA:AA:AA:AA:BB")


@test
async def zeroconf_during_onboarding(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _technove: MagicMock = Depends(mock_technove),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    onboarding: MagicMock = Depends(mock_onboarding),
) -> None:
    """Test we create a config entry when discovered during onboarding."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "AA:AA:AA:AA:AA:BB"},
            type="mock_type",
        ),
    )

    expect(result.get("title")).to_equal("TechnoVE Station")
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect(result.get("data")).to_equal({CONF_HOST: "192.168.1.123"})
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("AA:AA:AA:AA:AA:BB")

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(onboarding.mock_calls)).to_equal(1)


@test
async def zeroconf_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test we abort zeroconf flow on TechnoVE connection error."""
    technove.update.side_effect = TechnoVEConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "AA:AA:AA:AA:AA:BB"},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def user_station_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test we abort zeroconf flow if TechnoVE station already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "192.168.1.123"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def zeroconf_without_mac_station_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test we abort zeroconf flow if TechnoVE station already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def zeroconf_with_mac_station_exists_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    technove: MagicMock = Depends(mock_technove),
) -> None:
    """Test we abort zeroconf flow if TechnoVE station already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "AA:AA:AA:AA:AA:BB"},
            type="mock_type",
        ),
    )

    technove.update.assert_not_called()
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
