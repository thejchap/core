"""Tests for the eGauge config flow."""

from unittest.mock import MagicMock

from egauge_async.exceptions import EgaugeAuthenticationError, EgaugePermissionError
from httpx import ConnectError
from tryke import Depends, expect, fixture, test

from homeassistant.components.egauge.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.egauge._fixtures import (
    mock_config_entry,
    mock_egauge_client,
    mock_zeroconf,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def user_flow(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_egauge_client: MagicMock = Depends(mock_egauge_client),
) -> None:
    """Test the full happy path user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("egauge-home")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        }
    )
    expect(result["result"].unique_id).to_equal("ABC123456")


@test.cases(
    test.case("auth_error", EgaugeAuthenticationError, "invalid_auth"),
    test.case("permission_error", EgaugePermissionError, "missing_permission"),
    test.case("connect_error", ConnectError("Connection error"), "cannot_connect"),
    test.case("unknown", Exception("Unexpected error"), "unknown"),
)
async def user_flow_errors(
    side_effect: Exception,
    expected_error: str,
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    mock_egauge_client: MagicMock = Depends(mock_egauge_client),
) -> None:
    """Test user flow with various errors."""
    mock_egauge_client.get_device_serial_number.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "wrong",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": expected_error})

    mock_egauge_client.get_device_serial_number.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("egauge-home")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "192.168.1.100",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        }
    )
    expect(result["result"].unique_id).to_equal("ABC123456")


@test
async def user_flow_already_configured(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    _mock_zeroconf: MagicMock = Depends(mock_zeroconf),
    _mock_egauge_client: MagicMock = Depends(mock_egauge_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test configuration flow aborts when device is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "http://192.168.1.200",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "secret",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
    )

    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
