"""Test the Imeon Inverter config flow."""

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.imeon_inverter.const import DOMAIN
from homeassistant.config_entries import SOURCE_SSDP, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.ssdp import ATTR_UPNP_SERIAL

from ._fixtures import (
    TEST_DISCOVER,
    TEST_SERIAL,
    TEST_USER_INPUT,
    mock_async_setup_entry,
    mock_config_entry,
    mock_imeon_inverter,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_async_setup_entry),
    _imeon: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form_valid(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_async_setup_entry),
) -> None:
    """Test we get the form and the config is created with the good entries."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Imeon {TEST_SERIAL}")
    expect(result["data"]).to_equal(TEST_USER_INPUT)
    expect(result["result"].unique_id).to_equal(TEST_SERIAL)
    expect(setup_entry.call_count).to_equal(1)


@test
async def form_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    imeon: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    imeon.login.return_value = False

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    imeon.login.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test.cases(
    test.case("timeout_error", error=TimeoutError, expected="cannot_connect"),
    test.case("invalid_host", error=ValueError("Host invalid"), expected="invalid_host"),
    test.case("invalid_route", error=ValueError("Route invalid"), expected="invalid_route"),
    test.case("unknown_value_error", error=ValueError, expected="unknown"),
)
async def form_exception(
    error: Exception,
    expected: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    imeon: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    imeon.login.side_effect = error

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected})

    imeon.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def manual_setup_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that a flow with an existing id aborts."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def get_serial_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    imeon: MagicMock = Depends(mock_imeon_inverter),
) -> None:
    """Test the timeout error handling of getting the serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    imeon.get_serial.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    imeon.get_serial.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def ssdp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a ssdp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=TEST_DISCOVER,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = TEST_USER_INPUT.copy()
    user_input.pop(CONF_HOST)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"Imeon {TEST_SERIAL}")
    expect(result["data"]).to_equal(TEST_USER_INPUT)


@test
async def ssdp_already_exist(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that a ssdp discovery flow with an existing id aborts."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=TEST_DISCOVER,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def ssdp_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that a ssdp discovery aborts if serial is unknown."""
    data = deepcopy(TEST_DISCOVER)
    data.upnp.pop(ATTR_UPNP_SERIAL, None)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_SSDP},
        data=data,
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("cannot_connect")
