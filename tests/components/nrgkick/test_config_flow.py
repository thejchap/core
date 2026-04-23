"""Tests for the NRGkick config flow."""

from __future__ import annotations

from ipaddress import ip_address
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from nrgkick_api import (
    NRGkickAPIDisabledError,
    NRGkickAuthenticationError,
    NRGkickConnectionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.nrgkick.api import (
    NRGkickApiClientError,
    NRGkickApiClientInvalidResponseError,
)
from homeassistant.components.nrgkick.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.nrgkick._fixtures import (
    mock_async_zeroconf,
    mock_config_entry,
    mock_control_data,
    mock_info_data,
    mock_nrgkick_api,
    mock_setup_entry,
    mock_values_data,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf),
    _mse: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Wire mock_network + mock_async_zeroconf + mock_setup_entry for every test."""


ZEROCONF_DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.101"),
    ip_addresses=[ip_address("192.168.1.101")],
    hostname="nrgkick.local.",
    name="NRGkick Test._nrgkick._tcp.local.",
    port=80,
    properties={
        "serial_number": "TEST123456",
        "device_name": "NRGkick Test",
        "model_type": "NRGkick Gen2",
        "json_api_enabled": "1",
        "json_api_version": "v1",
    },
    type="_nrgkick._tcp.local.",
)

ZEROCONF_DISCOVERY_INFO_DISABLED_JSON_API = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.101"),
    ip_addresses=[ip_address("192.168.1.101")],
    hostname="nrgkick.local.",
    name="NRGkick Test._nrgkick._tcp.local.",
    port=80,
    properties={
        "serial_number": "TEST123456",
        "device_name": "NRGkick Test",
        "model_type": "NRGkick Gen2",
        "json_api_enabled": "0",
        "json_api_version": "v1",
    },
    type="_nrgkick._tcp.local.",
)

ZEROCONF_DISCOVERY_INFO_NO_SERIAL = ZeroconfServiceInfo(
    ip_address=ip_address("192.168.1.101"),
    ip_addresses=[ip_address("192.168.1.101")],
    hostname="nrgkick.local.",
    name="NRGkick Test._nrgkick._tcp.local.",
    port=80,
    properties={
        "device_name": "NRGkick Test",
        "model_type": "NRGkick Gen2",
        "json_api_enabled": "1",
        "json_api_version": "v1",
    },
    type="_nrgkick._tcp.local.",
)


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test we can set up successfully without credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("TEST123456")


@test
async def user_flow_with_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can setup when authentication is required."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
        }
    )
    expect(result["result"].unique_id).to_equal("TEST123456")
    mock_setup.assert_called_once()


@test.cases(
    test.case("http", "http://"),
    test.case("empty", ""),
)
async def form_invalid_host_input(
    url: str,
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test we handle invalid host input during normalization."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: url}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def form_fallback_title_when_device_name_missing(
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test we fall back to a default title when device name is missing."""
    api.get_info.return_value = {"general": {"serial_number": "ABC"}}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})


@test
async def form_invalid_response_when_serial_missing(
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
    info_data: dict[str, Any] = Depends(mock_info_data),
) -> None:
    """Test we handle invalid device info response."""
    api.get_info.return_value = {"general": {"device_name": "NRGkick"}}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_response"})

    api.get_info.return_value = info_data
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.100"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "invalid_response"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def user_flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test errors are handled and the flow can recover to CREATE_ENTRY."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("auth", NRGkickAuthenticationError, "invalid_auth"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "invalid_response"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def user_flow_auth_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test errors are handled and the flow can recover to CREATE_ENTRY."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")
    expect(result["errors"]).to_equal({})

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test we handle already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_auth_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test we handle already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")
    expect(result["errors"]).to_equal({})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test zeroconf discovery without credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")
    expect(result["description_placeholders"]).to_equal(
        {
            "name": "NRGkick Test",
            "device_ip": "192.168.1.101",
        }
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.101"})
    expect(result["result"].unique_id).to_equal("TEST123456")


@test
async def zeroconf_discovery_with_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
    mock_setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery flow (auth required)."""
    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")
    expect(result["description_placeholders"]).to_equal({"device_ip": "192.168.1.101"})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "test_user", CONF_PASSWORD: "test_pass"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.101",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
        }
    )
    expect(result["result"].unique_id).to_equal("TEST123456")
    mock_setup.assert_called_once()


@test.cases(
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def zeroconf_errors(
    exception: type[Exception],
    reason: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test zeroconf confirm step reports errors."""
    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def zeroconf_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_nrgkick_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test zeroconf discovery when device is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=ZEROCONF_DISCOVERY_INFO
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.101")


@test
async def zeroconf_json_api_disabled(
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test zeroconf discovery when JSON API is disabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO_DISABLED_JSON_API,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_enable_json_api")
    expect(result["description_placeholders"]).to_equal(
        {
            "name": "NRGkick Test",
            "device_ip": "192.168.1.101",
        }
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.101"})
    expect(result["result"].unique_id).to_equal("TEST123456")


@test
async def zeroconf_json_api_disabled_stale_mdns(
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test zeroconf discovery when JSON API is disabled."""
    api.test_connection.side_effect = NRGkickAPIDisabledError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_enable_json_api")
    expect(result["description_placeholders"]).to_equal(
        {
            "name": "NRGkick Test",
            "device_ip": "192.168.1.101",
        }
    )

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.101"})
    expect(result["result"].unique_id).to_equal("TEST123456")


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "invalid_response"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def zeroconf_json_api_disabled_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test zeroconf discovery when JSON API is disabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO_DISABLED_JSON_API,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_enable_json_api")
    expect(result["description_placeholders"]).to_equal(
        {
            "name": "NRGkick Test",
            "device_ip": "192.168.1.101",
        }
    )

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_enable_json_api")
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.101"})
    expect(result["result"].unique_id).to_equal("TEST123456")


@test
async def zeroconf_json_api_disabled_with_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test JSON API disabled flow that requires authentication afterwards."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO_DISABLED_JSON_API,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_enable_json_api")

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.101",
            CONF_USERNAME: "user",
            CONF_PASSWORD: "pass",
        }
    )


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("auth", NRGkickAuthenticationError, "invalid_auth"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def zeroconf_enable_json_api_auth_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test JSON API enable auth step reports errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO_DISABLED_JSON_API,
    )

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")
    expect(result["errors"]).to_equal({})

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("auth", NRGkickAuthenticationError, "invalid_auth"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def zeroconf_auth_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test zeroconf auth step reports errors."""
    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user_auth")

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def zeroconf_no_serial_number(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test zeroconf discovery without serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO_NO_SERIAL,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_serial_number")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "new_user", CONF_PASSWORD: "new_pass"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.100")
    expect(config_entry.data[CONF_USERNAME]).to_equal("new_user")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_pass")


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("auth", NRGkickAuthenticationError, "invalid_auth"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "invalid_response"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def reauth_flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reauthentication flow error handling and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauth_flow_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reauthentication aborts on unique ID mismatch."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    api.get_info.return_value = {
        "general": {"serial_number": "DIFFERENT123", "device_name": "Other"}
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reconfiguration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: ""}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.200")


@test
async def reconfigure_flow_with_credentials(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reconfiguration flow when authentication is required."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_auth")

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "new_user", CONF_PASSWORD: "new_pass"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.200")
    expect(config_entry.data[CONF_USERNAME]).to_equal("new_user")
    expect(config_entry.data[CONF_PASSWORD]).to_equal("new_pass")


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "invalid_response"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def reconfigure_flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reconfiguration flow errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test.cases(
    test.case("json_disabled", NRGkickAPIDisabledError, "json_api_disabled"),
    test.case("auth", NRGkickAuthenticationError, "invalid_auth"),
    test.case("invalid_response", NRGkickApiClientInvalidResponseError, "invalid_response"),
    test.case("connection", NRGkickConnectionError, "cannot_connect"),
    test.case("generic", NRGkickApiClientError, "unknown"),
)
async def reconfigure_flow_auth_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reconfiguration auth step errors and recovery."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    api.test_connection.side_effect = NRGkickAuthenticationError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_auth")

    api.test_connection.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure_auth")
    expect(result["errors"]).to_equal({"base": error})

    api.test_connection.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: "user", CONF_PASSWORD: "pass"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reconfigure_flow_unique_id_mismatch(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test reconfiguration aborts on unique ID mismatch."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    api.get_info.return_value = {
        "general": {"serial_number": "DIFFERENT123", "device_name": "Other"}
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.200"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unique_id_mismatch")
