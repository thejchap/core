"""Test the bang_olufsen config_flow."""

from unittest.mock import AsyncMock, Mock

from aiohttp.client_exceptions import ClientConnectorError
from mozart_api.exceptions import ApiException
from tryke import Depends, expect, fixture, test

from homeassistant.components.bang_olufsen.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.bang_olufsen._fixtures import mock_mozart_client, mock_setup_entry
from tests.hass_fixtures import hass

from .const import (
    TEST_DATA_CREATE_ENTRY,
    TEST_DATA_USER,
    TEST_DATA_USER_INVALID,
    TEST_DATA_ZEROCONF,
    TEST_DATA_ZEROCONF_IPV6,
    TEST_DATA_ZEROCONF_NOT_MOZART,
)


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def config_flow_timeout_error(
    hass: HomeAssistant = Depends(hass),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle timeout_error."""
    mock_mozart_client.get_beolink_self.side_effect = TimeoutError()

    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=TEST_DATA_USER,
    )
    expect(result_user["type"] is FlowResultType.FORM).to_be(True)
    expect(result_user["errors"]).to_equal({"base": "timeout_error"})

    expect(mock_mozart_client.get_beolink_self.call_count).to_equal(1)


@test
async def config_flow_client_connector_error(
    hass: HomeAssistant = Depends(hass),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle client_connector_error."""
    mock_mozart_client.get_beolink_self.side_effect = ClientConnectorError(
        Mock(), Mock()
    )

    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=TEST_DATA_USER,
    )
    expect(result_user["type"] is FlowResultType.FORM).to_be(True)
    expect(result_user["errors"]).to_equal({"base": "client_connector_error"})

    expect(mock_mozart_client.get_beolink_self.call_count).to_equal(1)


@test
async def config_flow_invalid_ip(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle invalid_ip."""
    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=TEST_DATA_USER_INVALID,
    )
    expect(result_user["type"] is FlowResultType.FORM).to_be(True)
    expect(result_user["errors"]).to_equal({"base": "invalid_ip"})


@test
async def config_flow_api_exception(
    hass: HomeAssistant = Depends(hass),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle api_exception."""
    mock_mozart_client.get_beolink_self.side_effect = ApiException()

    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=TEST_DATA_USER,
    )
    expect(result_user["type"] is FlowResultType.FORM).to_be(True)
    expect(result_user["errors"]).to_equal({"base": "api_exception"})

    expect(mock_mozart_client.get_beolink_self.call_count).to_equal(1)


@test
async def config_flow(
    hass: HomeAssistant = Depends(hass),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test config flow."""
    result_init = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
        data=None,
    )

    expect(result_init["type"] is FlowResultType.FORM).to_be(True)
    expect(result_init["step_id"]).to_equal("user")

    result_user = await hass.config_entries.flow.async_configure(
        flow_id=result_init["flow_id"],
        user_input=TEST_DATA_USER,
    )

    expect(result_user["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result_user["data"]).to_equal(TEST_DATA_CREATE_ENTRY)

    expect(mock_mozart_client.get_beolink_self.call_count).to_equal(1)


@test
async def config_flow_zeroconf(
    hass: HomeAssistant = Depends(hass),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery."""
    result_zeroconf = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DATA_ZEROCONF,
    )

    expect(result_zeroconf["type"] is FlowResultType.FORM).to_be(True)
    expect(result_zeroconf["step_id"]).to_equal("zeroconf_confirm")

    result_confirm = await hass.config_entries.flow.async_configure(
        flow_id=result_zeroconf["flow_id"],
        user_input=TEST_DATA_USER,
    )

    expect(result_confirm["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result_confirm["data"]).to_equal(TEST_DATA_CREATE_ENTRY)

    expect(mock_mozart_client.get_beolink_self.call_count).to_equal(1)


@test
async def config_flow_zeroconf_not_mozart_device(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery of invalid device."""
    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DATA_ZEROCONF_NOT_MOZART,
    )

    expect(result_user["type"] is FlowResultType.ABORT).to_be(True)
    expect(result_user["reason"]).to_equal("not_mozart_device")


@test
async def config_flow_zeroconf_ipv6(
    hass: HomeAssistant = Depends(hass),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery with IPv6 IP address."""
    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DATA_ZEROCONF_IPV6,
    )

    expect(result_user["type"] is FlowResultType.ABORT).to_be(True)
    expect(result_user["reason"]).to_equal("ipv6_address")


@test
async def config_flow_zeroconf_invalid_ip(
    hass: HomeAssistant = Depends(hass),
    mock_mozart_client: AsyncMock = Depends(mock_mozart_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf discovery with invalid IP address."""
    mock_mozart_client.get_beolink_self.side_effect = ClientConnectorError(
        Mock(), Mock()
    )

    result_user = await hass.config_entries.flow.async_init(
        handler=DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=TEST_DATA_ZEROCONF,
    )

    expect(result_user["type"] is FlowResultType.ABORT).to_be(True)
    expect(result_user["reason"]).to_equal("invalid_address")
