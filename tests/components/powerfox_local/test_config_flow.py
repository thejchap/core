"""Test the Powerfox Local config flow."""

from __future__ import annotations

from datetime import UTC, datetime
from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from powerfox import LocalResponse, PowerfoxAuthenticationError, PowerfoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.powerfox_local.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import MOCK_API_KEY, MOCK_DEVICE_ID, MOCK_HOST

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_powerfox_local_client as mock_powerfox_local_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

MOCK_ZEROCONF_DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address(MOCK_HOST),
    ip_addresses=[ip_address(MOCK_HOST)],
    hostname="powerfox.local",
    name="Powerfox",
    port=443,
    type="_http._tcp",
    properties={"id": MOCK_DEVICE_ID},
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
    _client: AsyncMock = Depends(mock_powerfox_local_client_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire shared fixtures for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_local_client: AsyncMock = Depends(mock_powerfox_local_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(bool(result.get("errors"))).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(f"Poweropti ({MOCK_DEVICE_ID[-5:]})")
    expect(result.get("data")).to_equal(
        {CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY}
    )
    expect(result["result"].unique_id).to_equal(MOCK_DEVICE_ID)
    expect(len(mock_powerfox_local_client.value.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("zeroconf_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal(f"Poweropti ({MOCK_DEVICE_ID[-5:]})")
    expect(result.get("data")).to_equal(
        {CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY}
    )
    expect(result["result"].unique_id).to_equal(MOCK_DEVICE_ID)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("connection", PowerfoxConnectionError),
    test.case("auth", PowerfoxAuthenticationError),
)
async def zeroconf_discovery_errors(
    exception: Exception,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_local_client: AsyncMock = Depends(mock_powerfox_local_client_fx),
) -> None:
    """Test zeroconf discovery aborts on connection/auth errors."""
    mock_powerfox_local_client.value.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def zeroconf_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test zeroconf discovery aborts when already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test abort when setting up duplicate entry."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test.cases(
    test.case("connection", PowerfoxConnectionError, "cannot_connect"),
    test.case("auth", PowerfoxAuthenticationError, "invalid_auth"),
)
async def user_flow_exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_local_client: AsyncMock = Depends(mock_powerfox_local_client_fx),
) -> None:
    """Test exceptions during user config flow."""
    mock_powerfox_local_client.value.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    mock_powerfox_local_client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test re-authentication flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new-api-key")


@test.cases(
    test.case("connection", PowerfoxConnectionError, "cannot_connect"),
    test.case("auth", PowerfoxAuthenticationError, "invalid_auth"),
)
async def step_reauth_exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_local_client: AsyncMock = Depends(mock_powerfox_local_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test exceptions during re-authentication flow."""
    mock_powerfox_local_client.value.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    mock_powerfox_local_client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new-api-key")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguration flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.200")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal(MOCK_API_KEY)


@test.cases(
    test.case("connection", PowerfoxConnectionError, "cannot_connect"),
    test.case("auth", PowerfoxAuthenticationError, "invalid_auth"),
)
async def reconfigure_flow_exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_local_client: AsyncMock = Depends(mock_powerfox_local_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test exceptions during reconfiguration flow."""
    mock_powerfox_local_client.value.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    mock_powerfox_local_client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.200")


@test
async def reconfigure_flow_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_local_client: AsyncMock = Depends(mock_powerfox_local_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguration aborts on unique ID mismatch."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    mock_powerfox_local_client.value.return_value = LocalResponse(
        timestamp=datetime(2026, 2, 25, 10, 48, 51, tzinfo=UTC),
        power=111,
        energy_usage=1111111,
        energy_return=111111,
        energy_usage_high_tariff=111111,
        energy_usage_low_tariff=111111,
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: "different_api_key"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("unique_id_mismatch")
