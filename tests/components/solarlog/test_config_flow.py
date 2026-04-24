"""Test the solarlog config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from solarlog_cli.solarlog_exceptions import (
    SolarLogAuthenticationError,
    SolarLogConnectionError,
    SolarLogError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.solarlog.const import CONF_HAS_PWD, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry, mock_solarlog_connector, test_connect
from .const import HOST

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: None = Depends(test_connect),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_HAS_PWD: False},
    )

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal(HOST)
    expect(result2["data"][CONF_HOST]).to_equal("http://1.1.1.1")
    expect(result2["data"][CONF_HAS_PWD]).to_be(False)
    expect(len(setup.mock_calls)).to_equal(1)


@test
async def user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: None = Depends(test_connect),
    _connector: AsyncMock = Depends(mock_solarlog_connector),
    setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_HAS_PWD: False}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(HOST)
    expect(result["data"][CONF_HOST]).to_equal(HOST)
    expect(len(setup.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "connect_then_auth",
        exception1=SolarLogConnectionError,
        error1={CONF_HOST: "cannot_connect"},
        exception2=SolarLogAuthenticationError,
        error2={CONF_HOST: "password_error"},
    ),
    test.case(
        "unknown_twice",
        exception1=SolarLogError,
        error1={CONF_HOST: "unknown"},
        exception2=SolarLogError,
        error2={CONF_HOST: "unknown"},
    ),
)
async def form_exceptions(
    exception1: type[Exception],
    error1: dict[str, str],
    exception2: type[Exception],
    error2: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connector: AsyncMock = Depends(mock_solarlog_connector),
) -> None:
    """Test we can handle Form exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    connector.test_connection.side_effect = exception1

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: HOST, CONF_HAS_PWD: False}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(error1)

    connector.test_connection.side_effect = None
    connector.test_extended_data_available.side_effect = exception2

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: HOST, CONF_HAS_PWD: True}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("password")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "pwd"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("password")
    expect(result["errors"]).to_equal(error2)

    connector.test_extended_data_available.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_PASSWORD: "pwd"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(HOST)
    expect(result["data"][CONF_PASSWORD]).to_equal("pwd")


@test
async def abort_if_already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _connect: None = Depends(test_connect),
) -> None:
    """Test we abort if the device is already setup."""
    MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST}).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: HOST, CONF_HAS_PWD: False},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case("with_password", has_password=True, password="pwd"),
    test.case("no_password", has_password=False, password=""),
)
async def reconfigure_flow(
    has_password: bool,
    password: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup: AsyncMock = Depends(mock_setup_entry),
    _connector: AsyncMock = Depends(mock_solarlog_connector),
) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        data={CONF_HOST: HOST, CONF_HAS_PWD: False},
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HAS_PWD: True, CONF_PASSWORD: password}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(len(setup.mock_calls)).to_equal(1)

    entry = hass.config_entries.async_get_entry(entry.entry_id)
    expect(entry is not None).to_be(True)
    expect(entry.title).to_equal(HOST)
    expect(entry.data[CONF_HAS_PWD]).to_equal(has_password)
    expect(entry.data[CONF_PASSWORD]).to_equal(password)


@test.cases(
    test.case(
        "password_error",
        exception=SolarLogAuthenticationError,
        error={CONF_HOST: "password_error"},
    ),
    test.case(
        "unknown",
        exception=SolarLogError,
        error={CONF_HOST: "unknown"},
    ),
)
async def reauth(
    exception: type[Exception],
    error: dict[str, str],
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    connector: AsyncMock = Depends(mock_solarlog_connector),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth-flow works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        data={
            CONF_HOST: HOST,
            CONF_HAS_PWD: True,
            CONF_PASSWORD: "pwd",
        },
        minor_version=3,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    connector.test_extended_data_available.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "other_pwd"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal(error)

    connector.test_extended_data_available.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "other_pwd"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_PASSWORD]).to_equal("other_pwd")
