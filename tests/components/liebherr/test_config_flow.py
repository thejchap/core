"""Test the liebherr config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from pyliebherrhomeapi.exceptions import (
    LiebherrAuthenticationError,
    LiebherrConnectionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.liebherr.const import DOMAIN
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_liebherr_client,
    mock_setup_entry,
    patch_refresh_delay,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_API_KEY = "test-api-key"
MOCK_USER_INPUT = {CONF_API_KEY: MOCK_API_KEY}

MOCK_ZEROCONF_SERVICE_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.100"),
    ip_addresses=[ip_address("192.168.1.100")],
    port=80,
    hostname="liebherr-device.local.",
    type="_http._tcp.local.",
    name="liebherr-fridge._http._tcp.local.",
    properties={},
)


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _pr: None = Depends(patch_refresh_delay),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Liebherr")
    expect(result.get("data")).to_equal(MOCK_USER_INPUT)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        LiebherrAuthenticationError("Invalid"),
        "invalid_auth",
    ),
    test.case(
        "cannot_connect",
        LiebherrConnectionError("Failed"),
        "cannot_connect",
    ),
    test.case("unknown", Exception("Unexpected"), "unknown"),
)
async def form_errors_with_recovery(
    side_effect: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
) -> None:
    """Test error handling with successful recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({})

    mock_liebherr_client.get_devices.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": expected_error})

    mock_liebherr_client.get_devices.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Liebherr")
    expect(result.get("data")).to_equal(MOCK_USER_INPUT)


@test
async def form_no_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
) -> None:
    """Test we handle no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)

    mock_liebherr_client.get_devices.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("no_devices")


@test
async def form_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
) -> None:
    """Test zeroconf discovery triggers the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("Liebherr")
    expect(result.get("data")).to_equal(MOCK_USER_INPUT)


@test
async def zeroconf_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery aborts if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_SERVICE_INFO,
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    new_api_key = "new-api-key"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: new_api_key}
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal(new_api_key)


@test.cases(
    test.case(
        "invalid_auth",
        LiebherrAuthenticationError("Invalid"),
        "invalid_auth",
    ),
    test.case(
        "cannot_connect",
        LiebherrConnectionError("Failed"),
        "cannot_connect",
    ),
    test.case("unknown", Exception("Unexpected"), "unknown"),
)
async def reauth_flow_errors_with_recovery(
    side_effect: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_liebherr_client: MagicMock = Depends(mock_liebherr_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow error handling with successful recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    mock_liebherr_client.get_devices.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new-api-key"}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": expected_error})

    mock_liebherr_client.get_devices.side_effect = None
    new_api_key = "new-api-key-recovered"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: new_api_key}
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal(new_api_key)
