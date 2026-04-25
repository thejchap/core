"""Tests for the Daikin config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from aiohttp import ClientError, web_exceptions
from pydaikin.exceptions import DaikinException
from tryke import Depends, expect, fixture, test

from homeassistant.components.daikin.const import KEY_MAC
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_daikin, mock_daikin_discovery, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MAC = "AABBCCDDEEFF"
HOST = "127.0.0.1"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _daikin: MagicMock = Depends(mock_daikin),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(HOST)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(result["data"][KEY_MAC]).to_equal(MAC)


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _daikin: MagicMock = Depends(mock_daikin),
) -> None:
    """Test we abort if Daikin is already setup."""
    MockConfigEntry(domain="daikin", unique_id=MAC).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, KEY_MAC: MAC},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("timeout", s_effect=TimeoutError, reason="cannot_connect"),
    test.case("client_error", s_effect=ClientError, reason="cannot_connect"),
    test.case(
        "forbidden", s_effect=web_exceptions.HTTPForbidden, reason="invalid_auth"
    ),
    test.case("daikin_exc", s_effect=DaikinException, reason="unknown"),
    test.case("exception", s_effect=Exception, reason="unknown"),
)
async def device_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    daikin: MagicMock = Depends(mock_daikin),
    *,
    s_effect: type[Exception],
    reason: str,
) -> None:
    """Test device abort."""
    daikin.side_effect = s_effect

    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, KEY_MAC: MAC},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": reason})
    expect(result["step_id"]).to_equal("user")


@test
async def api_password_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test device abort."""
    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_API_KEY: "aa", CONF_PASSWORD: "aa"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "api_password"})
    expect(result["step_id"]).to_equal("user")


_ZEROCONF_DATA = ZeroconfServiceInfo(
    ip_address=ip_address(HOST),
    ip_addresses=[ip_address(HOST)],
    hostname="mock_hostname",
    name="mock_name",
    port=None,
    properties={},
    type="mock_type",
)


@test.cases(
    test.case("zeroconf", source=SOURCE_ZEROCONF, data=_ZEROCONF_DATA, unique_id=MAC),
)
async def discovery_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _daikin: MagicMock = Depends(mock_daikin),
    _discovery: MagicMock = Depends(mock_daikin_discovery),
    *,
    source: str,
    data: ZeroconfServiceInfo,
    unique_id: str,
) -> None:
    """Test discovery/zeroconf step."""
    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": source},
        data=data,
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    MockConfigEntry(domain="daikin", unique_id=unique_id).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": SOURCE_USER, "unique_id": unique_id},
        data={CONF_HOST: HOST},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    result = await hass.config_entries.flow.async_init(
        "daikin",
        context={"source": source},
        data=data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")
