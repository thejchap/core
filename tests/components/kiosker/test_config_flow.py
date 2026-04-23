"""Test the Kiosker config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from kiosker import (
    AuthenticationError,
    BadRequestError,
    ConnectionError,
    IPAuthenticationError,
    PingError,
    TLSVerificationError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.kiosker.const import CONF_API_TOKEN, DOMAIN
from homeassistant.const import CONF_HOST, CONF_SSL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_config_entry, mock_kiosker_api, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.39"),
    ip_addresses=[ip_address("192.168.1.39")],
    hostname="python-test-device.local.",
    name="Kiosker Device._kiosker._tcp.local.",
    port=8081,
    properties={
        "uuid": "A98BE1CE-5FE7-4A8D-B2C3-123456789ABC",
        "app": "Kiosker",
        "version": "1.0.0",
        "ssl": "true",
    },
    type="_kiosker._tcp.local.",
)

DISCOVERY_INFO_NO_UUID = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.39"),
    ip_addresses=[ip_address("192.168.1.39")],
    hostname="kiosker-device.local.",
    name="Kiosker Device._kiosker._tcp.local.",
    port=8081,
    properties={"app": "Kiosker", "version": "1.0.0", "ssl": "false"},
    type="_kiosker._tcp.local.",
)


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def user_flow_creates_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_kiosker_api: MagicMock = Depends(mock_kiosker_api),
) -> None:
    """Test the full user config flow creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Kiosker A98BE1CE")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        }
    )
    expect(result2["result"].unique_id).to_equal("A98BE1CE-5FE7-4A8D-B2C3-123456789ABC")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("connection_error", ConnectionError(), "cannot_connect"),
    test.case("auth_error", AuthenticationError(), "invalid_auth"),
    test.case("ip_auth_error", IPAuthenticationError(), "invalid_ip_auth"),
    test.case("tls_error", TLSVerificationError(), "tls_error"),
    test.case("bad_request", BadRequestError(), "bad_request"),
    test.case("ping_error", PingError(), "cannot_connect"),
    test.case("unknown", Exception(), "unknown"),
)
async def user_flow_errors_and_recovery(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_kiosker_api: MagicMock = Depends(mock_kiosker_api),
) -> None:
    """Test user flow handles all validation errors and can recover."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_kiosker_api.status.side_effect = exception
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error})

    mock_kiosker_api.status.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.100",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_kiosker_api: MagicMock = Depends(mock_kiosker_api),
) -> None:
    """Test the zeroconf discovery happy flow creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "name": "python-test-device (A98BE1CE)",
            "host": "192.168.1.39",
        }
    )
    schema_keys = list(result["data_schema"].schema.keys())
    expect(any(key.schema == CONF_API_TOKEN for key in schema_keys)).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "test-token",
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("Kiosker A98BE1CE")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.39",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        }
    )
    expect(result2["result"].unique_id).to_equal("A98BE1CE-5FE7-4A8D-B2C3-123456789ABC")


@test
async def zeroconf_error_and_recovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_kiosker_api: MagicMock = Depends(mock_kiosker_api),
) -> None:
    """Test zeroconf discovery handles errors and recovers."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    mock_kiosker_api.status.side_effect = ConnectionError()
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "test-token",
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})

    mock_kiosker_api.status.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_API_TOKEN: "test-token",
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf_no_uuid(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery without UUID aborts with cannot_connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO_NO_UUID,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")


@test
async def abort_if_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_kiosker_api: MagicMock = Depends(mock_kiosker_api),
) -> None:
    """Test we abort if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.200",
            CONF_API_TOKEN: "test-token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def zeroconf_abort_if_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort zeroconf discovery if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_no_device_id(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_kiosker_api: MagicMock = Depends(mock_kiosker_api),
) -> None:
    """Test user flow shows cannot_connect error when device reports no device ID."""
    mock_kiosker_api.status.return_value.device_id = None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "10.0.1.5",
            CONF_API_TOKEN: "test_token",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})
