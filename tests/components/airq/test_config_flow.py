"""Test the air-Q config flow."""

from ipaddress import IPv4Address
from unittest.mock import AsyncMock

from aioairq import InvalidAuth
from aiohttp.client_exceptions import ClientConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.airq.const import (
    CONF_CLIP_NEGATIVE,
    CONF_RETURN_AVERAGE,
    DOMAIN,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.components.airq._fixtures import mock_airq, mock_setup_entry
from tests.hass_fixtures import hass, mock_network

from .common import TEST_DEVICE_INFO, TEST_USER_DATA


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


ZEROCONF_DISCOVERY = ZeroconfServiceInfo(
    ip_address=IPv4Address("192.168.0.123"),
    ip_addresses=[IPv4Address("192.168.0.123")],
    port=80,
    hostname="airq.local.",
    type="_http._tcp.local.",
    name="air-Q._http._tcp.local.",
    properties={"device": "air-q", "devicename": "My air-Q", "id": "test-serial-123"},
)

DEFAULT_OPTIONS = {
    CONF_CLIP_NEGATIVE: True,
    CONF_RETURN_AVERAGE: True,
}


@test
async def form(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["errors"] is None).to_be(True)

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_USER_DATA,
    )
    await hass.async_block_till_done()

    expect(result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result2["title"]).to_equal(TEST_DEVICE_INFO["name"])
    expect(result2["data"]).to_equal(TEST_USER_DATA)


@test
async def form_invalid_auth(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_airq.validate.side_effect = InvalidAuth
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_DATA | {CONF_PASSWORD: "wrong_password"}
    )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def form_cannot_connect(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    mock_airq.validate.side_effect = ClientConnectionError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_DATA
    )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test that errors are shown when duplicates are added."""
    MockConfigEntry(
        data=TEST_USER_DATA,
        domain=DOMAIN,
        unique_id=TEST_DEVICE_INFO["id"],
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_DATA
    )
    expect(result2["type"] is FlowResultType.ABORT).to_be(True)
    expect(result2["reason"]).to_equal("already_configured")


@test.cases(
    test.case("empty", {}),
    test.case("return_average_false", {CONF_RETURN_AVERAGE: False}),
    test.case("clip_negative_false", {CONF_CLIP_NEGATIVE: False}),
)
async def options_flow(
    user_input: dict,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that the options flow works."""
    entry = MockConfigEntry(
        domain=DOMAIN, data=TEST_USER_DATA, unique_id=TEST_DEVICE_INFO["id"]
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("init")
    expect(entry.options).to_equal({})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=user_input
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expected = DEFAULT_OPTIONS | user_input
    expect(result["data"]).to_equal(expected)
    expect(entry.options).to_equal(expected)


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test zeroconf discovery and successful setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "password"},
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("My air-Q")
    expect(result["result"].unique_id).to_equal("test-serial-123")
    expect(result["data"]).to_equal(
        {CONF_IP_ADDRESS: "192.168.0.123", CONF_PASSWORD: "password"}
    )


@test.cases(
    test.case("invalid_auth", InvalidAuth, "invalid_auth"),
    test.case("cannot_connect", ClientConnectionError, "cannot_connect"),
)
async def zeroconf_discovery_errors(
    side_effect: type[Exception],
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test zeroconf discovery with invalid password or connection error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("discovery_confirm")

    mock_airq.validate.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "wrong_password"},
    )

    expect(result2["type"] is FlowResultType.FORM).to_be(True)
    expect(result2["errors"]).to_equal({"base": expected_error})

    mock_airq.validate.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_PASSWORD: "correct_password"},
    )
    await hass.async_block_till_done()

    expect(result3["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result3["title"]).to_equal("My air-Q")
    expect(result3["data"]).to_equal(
        {CONF_IP_ADDRESS: "192.168.0.123", CONF_PASSWORD: "correct_password"}
    )


@test
async def zeroconf_discovery_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test zeroconf discovery aborts if device is already configured."""
    MockConfigEntry(
        data=TEST_USER_DATA,
        domain=DOMAIN,
        unique_id="test-serial-123",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")


@test
async def zeroconf_updates_ip_on_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test zeroconf updates the IP address if device is already configured."""
    entry = MockConfigEntry(
        data={CONF_IP_ADDRESS: "192.168.0.1", CONF_PASSWORD: "password"},
        domain=DOMAIN,
        unique_id="test-serial-123",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_IP_ADDRESS]).to_equal("192.168.0.123")


@test
async def user_flow_succeeds_during_zeroconf_discovery(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test manual user flow does not abort when a zeroconf flow is in progress."""
    zeroconf_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("192.168.0.123"),
            ip_addresses=[IPv4Address("192.168.0.123")],
            port=80,
            hostname="airq.local.",
            type="_http._tcp.local.",
            name="air-Q._http._tcp.local.",
            properties={
                "device": "air-q",
                "devicename": "My air-Q",
                "id": TEST_DEVICE_INFO["id"],
            },
        ),
    )
    expect(zeroconf_result["type"] is FlowResultType.FORM).to_be(True)
    expect(zeroconf_result["step_id"]).to_equal("discovery_confirm")

    user_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(user_result["type"] is FlowResultType.FORM).to_be(True)

    user_result2 = await hass.config_entries.flow.async_configure(
        user_result["flow_id"], TEST_USER_DATA
    )
    await hass.async_block_till_done()

    expect(user_result2["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(user_result2["title"]).to_equal(TEST_DEVICE_INFO["name"])
    expect(user_result2["data"]).to_equal(TEST_USER_DATA)

    ongoing_flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    expect(not ongoing_flows).to_be(True)


@test
async def zeroconf_discovery_missing_id(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_airq: AsyncMock = Depends(mock_airq),
) -> None:
    """Test zeroconf discovery aborts if device ID is missing from properties."""
    discovery_info = ZeroconfServiceInfo(
        ip_address=IPv4Address("192.168.0.123"),
        ip_addresses=[IPv4Address("192.168.0.123")],
        port=80,
        hostname="airq.local.",
        type="_http._tcp.local.",
        name="air-Q._http._tcp.local.",
        properties={"device": "air-q", "devicename": "My air-Q"},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info,
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("incomplete_discovery")
