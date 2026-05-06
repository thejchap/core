"""Test the slide_local config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock

from goslideapi.goslideapi import (
    AuthenticationFailed,
    ClientConnectionError,
    ClientTimeoutError,
    DigestAuthCalcError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.slide_local.const import CONF_INVERT_POSITION, DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_API_VERSION, CONF_HOST, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import get_data, setup_platform
from ._fixtures import mock_config_entry, mock_setup_entry, mock_slide_api
from .const import HOST

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_ZEROCONF_DATA = ZeroconfServiceInfo(
    ip_address=ip_address("127.0.0.2"),
    ip_addresses=[ip_address("127.0.0.2")],
    hostname="Slide-1234567890AB.local.",
    name="Slide-1234567890AB._http._tcp.local.",
    port=80,
    properties={
        "id": "slide-1234567890AB",
        "arch": "esp32",
        "app": "slide",
        "fw_version": "2.0.0-1683059251",
        "fw_id": "20230502-202745",
    },
    type="mock_type",
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(HOST)
    expect(result2["data"][CONF_HOST]).to_equal(HOST)
    expect(result2["data"][CONF_PASSWORD]).to_equal("pwd")
    expect(result2["data"][CONF_API_VERSION]).to_equal(2)
    expect(result2["result"].unique_id).to_equal("12:34:56:78:90:ab")
    expect(bool(result2["options"][CONF_INVERT_POSITION])).to_be(False)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_api_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    slide_api: AsyncMock = Depends(mock_slide_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    slide_api.slide_info.side_effect = [
        None,
        get_data(),
    ]

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(HOST)
    expect(result2["data"][CONF_HOST]).to_equal(HOST)
    expect(result2["data"][CONF_PASSWORD]).to_equal("pwd")
    expect(result2["data"][CONF_API_VERSION]).to_equal(1)
    expect(result2["result"].unique_id).to_equal("12:34:56:78:90:ab")
    expect(bool(result2["options"][CONF_INVERT_POSITION])).to_be(False)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def user_api_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    slide_api: AsyncMock = Depends(mock_slide_api),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    slide_api.slide_info.side_effect = [None, None]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("unknown")

    slide_api.slide_info.side_effect = [
        None,
        get_data(),
    ]

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(HOST)
    expect(result2["data"][CONF_HOST]).to_equal(HOST)
    expect(result2["data"][CONF_PASSWORD]).to_equal("pwd")
    expect(result2["data"][CONF_API_VERSION]).to_equal(1)
    expect(result2["result"].unique_id).to_equal("12:34:56:78:90:ab")
    expect(bool(result2["options"][CONF_INVERT_POSITION])).to_be(False)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("client_connection", exception=ClientConnectionError, error="cannot_connect"),
    test.case("client_timeout", exception=ClientTimeoutError, error="cannot_connect"),
    test.case("auth_failed", exception=AuthenticationFailed, error="invalid_auth"),
    test.case("digest_auth", exception=DigestAuthCalcError, error="invalid_auth"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def api_1_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    slide_api: AsyncMock = Depends(mock_slide_api),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test we can handle Form exceptions for api 1."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    slide_api.slide_info.side_effect = [None, exception]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal(error)

    slide_api.slide_info.side_effect = [
        None,
        get_data(),
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("client_connection", exception=ClientConnectionError, error="cannot_connect"),
    test.case("client_timeout", exception=ClientTimeoutError, error="cannot_connect"),
    test.case("auth_failed", exception=AuthenticationFailed, error="invalid_auth"),
    test.case("digest_auth", exception=DigestAuthCalcError, error="invalid_auth"),
    test.case("unknown", exception=Exception, error="unknown"),
)
async def api_2_exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    slide_api: AsyncMock = Depends(mock_slide_api),
    *,
    exception: type[Exception],
    error: str,
) -> None:
    """Test we can handle Form exceptions for api 2."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    slide_api.slide_info.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal(error)

    slide_api.slide_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
) -> None:
    """Test we abort if the device is already setup."""
    MockConfigEntry(domain=DOMAIN, unique_id="12:34:56:78:90:ab").add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure flow options."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "127.0.0.3",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(len(setup_entry.mock_calls)).to_equal(1)

    entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.data[CONF_HOST]).to_equal("127.0.0.3")


@test
async def zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a flow from discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=MOCK_ZEROCONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("zeroconf_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("127.0.0.2")
    expect(result["data"][CONF_HOST]).to_equal("127.0.0.2")
    expect(bool(result["options"][CONF_INVERT_POSITION])).to_be(False)
    expect(result["result"].unique_id).to_equal("12:34:56:78:90:ab")


@test
async def zeroconf_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test starting a flow from discovery."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: HOST}, unique_id="12:34:56:78:90:ab"
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=MOCK_ZEROCONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(entries[0].data[CONF_HOST]).to_equal(HOST)


@test
async def zeroconf_update_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test updating an existing entry from discovery."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.3"}, unique_id="12:34:56:78:90:ab"
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=MOCK_ZEROCONF_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(entries[0].data[CONF_HOST]).to_equal(HOST)


@test.cases(
    test.case("client_connection", exception=ClientConnectionError),
    test.case("client_timeout", exception=ClientTimeoutError),
    test.case("auth_failed", exception=AuthenticationFailed),
    test.case("digest_auth", exception=DigestAuthCalcError),
    test.case("unknown", exception=Exception),
)
async def zeroconf_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    slide_api: AsyncMock = Depends(mock_slide_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: type[Exception],
) -> None:
    """Test starting a flow from discovery."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "slide_host"}, unique_id="12:34:56:78:90:cd"
    ).add_to_hass(hass)

    slide_api.slide_info.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=MOCK_ZEROCONF_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("discovery_connection_failed")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_slide_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test options flow works correctly."""
    await setup_platform(hass, config_entry, [Platform.COVER])

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_INVERT_POSITION: True,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal(
        {
            CONF_INVERT_POSITION: True,
        }
    )
