"""Test the RabbitAir config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.rabbitair.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    rabbitair_connect as rabbitair_connect_fx,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_HOST = "1.1.1.1"
TEST_NAME = "abcdef1234_123456789012345678"
TEST_TOKEN = "0123456789abcdef0123456789abcdef"
TEST_MAC = "01:23:45:67:89:AB"
TEST_UNIQUE_ID = format_mac(TEST_MAC)
TEST_TITLE = "Rabbit Air"

ZEROCONF_DATA = ZeroconfServiceInfo(
    ip_address=ip_address(TEST_HOST),
    ip_addresses=[ip_address(TEST_HOST)],
    port=9009,
    hostname=f"{TEST_NAME}.local.",
    type="_rabbitair._udp.local.",
    name=f"{TEST_NAME}._rabbitair._udp.local.",
    properties={"id": TEST_MAC.replace(":", "")},
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
) -> None:
    """Wire mock_network + mock_async_zeroconf for every test."""


@test
async def form(
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: None = Depends(rabbitair_connect_fx),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "homeassistant.components.rabbitair.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_ACCESS_TOKEN: TEST_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_TITLE)
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_ACCESS_TOKEN: TEST_TOKEN,
            CONF_MAC: TEST_MAC,
        }
    )
    expect(result2["result"].unique_id).to_equal(TEST_UNIQUE_ID)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_access_token", error_type=ValueError, base_value="invalid_access_token"),
    test.case("invalid_host", error_type=OSError, base_value="invalid_host"),
    test.case("timeout_connect", error_type=TimeoutError, base_value="timeout_connect"),
    test.case("cannot_connect", error_type=Exception, base_value="cannot_connect"),
)
async def form_cannot_connect(
    error_type: type[Exception],
    base_value: str,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "rabbitair.UdpClient.get_info",
        side_effect=error_type,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_ACCESS_TOKEN: TEST_TOKEN,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": base_value})


@test
async def form_unknown_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "homeassistant.components.rabbitair.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_ACCESS_TOKEN: TEST_TOKEN,
            },
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: None = Depends(rabbitair_connect_fx),
) -> None:
    """Test zeroconf discovery setup flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=ZEROCONF_DATA
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    with patch(
        "homeassistant.components.rabbitair.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_NAME + ".local",
                CONF_ACCESS_TOKEN: TEST_TOKEN,
            },
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(TEST_TITLE)
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: TEST_NAME + ".local",
            CONF_ACCESS_TOKEN: TEST_TOKEN,
            CONF_MAC: TEST_MAC,
        }
    )
    expect(result2["result"].unique_id).to_equal(TEST_UNIQUE_ID)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=ZEROCONF_DATA
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
