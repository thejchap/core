"""Tests for the Iskra config flow."""

from unittest.mock import AsyncMock, MagicMock

from pyiskra.exceptions import (
    DeviceConnectionError,
    DeviceTimeoutError,
    InvalidResponseCode,
    NotAuthorised,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.iskra import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_ADDRESS,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_pyiskra_modbus, mock_pyiskra_rest, mock_setup_entry

from .const import (
    HOST,
    MODBUS_ADDRESS,
    MODBUS_PORT,
    PASSWORD,
    PQ_MODEL,
    SERIAL,
    SG_MODEL,
    USERNAME,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_rest_no_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pyiskra_rest: MagicMock = Depends(mock_pyiskra_rest),
) -> None:
    """Test the user flow with Rest API protocol."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(SG_MODEL)
    expect(result["data"]).to_equal({CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"})


@test
async def user_rest_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyiskra_rest: MagicMock = Depends(mock_pyiskra_rest),
) -> None:
    """Test the user flow with Rest API protocol and authentication required."""
    pyiskra_rest.side_effect = NotAuthorised

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("authentication")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": "invalid_auth"})
    expect(result["step_id"]).to_equal("authentication")

    pyiskra_rest.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(SG_MODEL)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: HOST,
            CONF_PROTOCOL: "rest_api",
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        }
    )


@test
async def user_modbus(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pyiskra_modbus: MagicMock = Depends(mock_pyiskra_modbus),
) -> None:
    """Test the user flow with Modbus TCP protocol."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "modbus_tcp"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("modbus_tcp")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(PQ_MODEL)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: HOST,
            CONF_PROTOCOL: "modbus_tcp",
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        }
    )


@test
async def modbus_abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pyiskra_modbus: MagicMock = Depends(mock_pyiskra_modbus),
) -> None:
    """Test we abort if Iskra is already setup."""
    MockConfigEntry(domain=DOMAIN, unique_id=SERIAL).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PROTOCOL: "modbus_tcp"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("modbus_tcp")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def rest_api_abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pyiskra_rest: MagicMock = Depends(mock_pyiskra_rest),
) -> None:
    """Test we abort if Iskra is already setup."""
    MockConfigEntry(domain=DOMAIN, unique_id=SERIAL).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("connection_error", s_effect=DeviceConnectionError, reason="cannot_connect"),
    test.case("timeout_error", s_effect=DeviceTimeoutError, reason="cannot_connect"),
    test.case("invalid_response", s_effect=InvalidResponseCode, reason="cannot_connect"),
    test.case("unknown_exception", s_effect=Exception, reason="unknown"),
)
async def modbus_device_error(
    s_effect: type[Exception],
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyiskra_modbus: MagicMock = Depends(mock_pyiskra_modbus),
) -> None:
    """Test device error with Modbus TCP protocol."""
    pyiskra_modbus.side_effect = s_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PROTOCOL: "modbus_tcp"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("modbus_tcp")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("modbus_tcp")
    expect(result["errors"]).to_equal({"base": reason})

    pyiskra_modbus.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(PQ_MODEL)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: HOST,
            CONF_PROTOCOL: "modbus_tcp",
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        }
    )


@test.cases(
    test.case("connection_error", s_effect=DeviceConnectionError, reason="cannot_connect"),
    test.case("timeout_error", s_effect=DeviceTimeoutError, reason="cannot_connect"),
    test.case("invalid_response", s_effect=InvalidResponseCode, reason="cannot_connect"),
    test.case("unknown_exception", s_effect=Exception, reason="unknown"),
)
async def rest_device_error(
    s_effect: type[Exception],
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyiskra_rest: MagicMock = Depends(mock_pyiskra_rest),
) -> None:
    """Test device error with Modbus TCP protocol."""
    pyiskra_rest.side_effect = s_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": reason})

    pyiskra_rest.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["result"].unique_id).to_equal(SERIAL)
    expect(result["title"]).to_equal(SG_MODEL)
    expect(result["data"]).to_equal({CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"})
