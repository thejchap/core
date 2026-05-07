"""Test the Powerfox Local config flow."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

from powerfox import LocalResponse, PowerfoxAuthenticationError, PowerfoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.powerfox_local.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import MOCK_API_KEY, MOCK_DEVICE_ID, MOCK_HOST
from ._fixtures import (
    mock_config_entry,
    mock_powerfox_local_client,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_ZEROCONF_DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=MOCK_HOST,
    ip_addresses=[MOCK_HOST],
    hostname="powerfox.local",
    name="Powerfox",
    port=443,
    type="_http._tcp",
    properties={"id": MOCK_DEVICE_ID},
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(not result.get("errors")).to_be(True)

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
    expect(len(client.value.mock_calls)).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
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
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("connection_error", exception=PowerfoxConnectionError),
    test.case("auth_error", exception=PowerfoxAuthenticationError),
)
async def zeroconf_discovery_errors(
    exception: type[Exception],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
) -> None:
    """Test zeroconf discovery aborts on connection/auth errors."""
    client.value.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("cannot_connect")


@test
async def zeroconf_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery aborts when already configured."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test abort when setting up duplicate entry."""
    config_entry.add_to_hass(hass)
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
    test.case("connection_error", exception=PowerfoxConnectionError, error="cannot_connect"),
    test.case("auth_error", exception=PowerfoxAuthenticationError, error="invalid_auth"),
)
async def user_flow_exceptions(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test exceptions during user config flow."""
    client.value.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: MOCK_HOST, CONF_API_KEY: MOCK_API_KEY},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def step_reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test re-authentication flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(config_entry.data[CONF_API_KEY]).to_equal("new-api-key")


@test.cases(
    test.case("connection_error", exception=PowerfoxConnectionError, error="cannot_connect"),
    test.case("auth_error", exception=PowerfoxAuthenticationError, error="invalid_auth"),
)
async def step_reauth_exceptions(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test exceptions during re-authentication flow."""
    client.value.side_effect = exception
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_API_KEY: "new-api-key"},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(config_entry.data[CONF_API_KEY]).to_equal("new-api-key")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.200")
    expect(config_entry.data[CONF_API_KEY]).to_equal(MOCK_API_KEY)


@test.cases(
    test.case("connection_error", exception=PowerfoxConnectionError, error="cannot_connect"),
    test.case("auth_error", exception=PowerfoxAuthenticationError, error="invalid_auth"),
)
async def reconfigure_flow_exceptions(
    exception: type[Exception],
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test exceptions during reconfiguration flow."""
    client.value.side_effect = exception
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    client.value.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.200", CONF_API_KEY: MOCK_API_KEY},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")

    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.200")


@test
async def reconfigure_flow_unique_id_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfiguration aborts on unique ID mismatch."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    client.value.return_value = LocalResponse(
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
