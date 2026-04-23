"""Tests for the OpenRGB config flow."""

from __future__ import annotations

import socket
from unittest.mock import AsyncMock, MagicMock

from openrgb.utils import OpenRGBDisconnected, SDKVersionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.openrgb.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_openrgb_client as mock_openrgb_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
) -> None:
    """Test the full user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Test Computer",
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 6742,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Computer")
    expect(result["data"]).to_equal(
        {
            CONF_NAME: "Test Computer",
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 6742,
        }
    )


@test.cases(
    test.case("connection_refused", ConnectionRefusedError, "cannot_connect"),
    test.case("openrgb_disconnected", OpenRGBDisconnected, "cannot_connect"),
    test.case("timeout_error", TimeoutError, "cannot_connect"),
    test.case("gaierror", socket.gaierror, "cannot_connect"),
    test.case("sdk_version_error", SDKVersionError, "cannot_connect"),
    test.case("runtime_error", RuntimeError("Test error"), "unknown"),
)
async def user_flow_errors(
    exception: type[Exception] | Exception,
    error_key: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
) -> None:
    """Test user flow with various errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    mock_openrgb_client.client_class_mock.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "Test Server", CONF_HOST: "127.0.0.1", CONF_PORT: 6742},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error_key})

    mock_openrgb_client.client_class_mock.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "Test Server", CONF_HOST: "127.0.0.1", CONF_PORT: 6742},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Test Server")
    expect(result["data"]).to_equal(
        {
            CONF_NAME: "Test Server",
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 6742,
        }
    )


@test
async def user_flow_already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test user flow when device is already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "Test Server", CONF_HOST: "127.0.0.1", CONF_PORT: 6742},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def user_flow_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test user flow when trying to add duplicate host/port combination."""
    mock_config_entry.add_to_hass(hass)

    other_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Other Computer",
        data={
            CONF_NAME: "Other Computer",
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 6743,
        },
        entry_id="01J0EXAMPLE0CONFIGENTRY01",
    )
    other_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Yet Another Computer",
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 6743,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test the reconfiguration flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 6743,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.100")
    expect(mock_config_entry.data[CONF_PORT]).to_equal(6743)


@test.cases(
    test.case("connection_refused", ConnectionRefusedError, "cannot_connect"),
    test.case("openrgb_disconnected", OpenRGBDisconnected, "cannot_connect"),
    test.case("timeout_error", TimeoutError, "cannot_connect"),
    test.case("gaierror", socket.gaierror, "cannot_connect"),
    test.case("sdk_version_error", SDKVersionError, "cannot_connect"),
    test.case("runtime_error", RuntimeError("Test error"), "unknown"),
)
async def reconfigure_flow_errors(
    exception: type[Exception] | Exception,
    error_key: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguration flow with various errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    mock_openrgb_client.client_class_mock.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 6743},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error_key})

    mock_openrgb_client.client_class_mock.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 6743},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data[CONF_HOST]).to_equal("192.168.1.100")
    expect(mock_config_entry.data[CONF_PORT]).to_equal(6743)


@test
async def reconfigure_flow_duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_openrgb_client: MagicMock = Depends(mock_openrgb_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfiguration flow when new config matches another existing entry."""
    mock_config_entry.add_to_hass(hass)

    other_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Other Computer",
        data={
            CONF_NAME: "Other Computer",
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 6743,
        },
        entry_id="01J0EXAMPLE0CONFIGENTRY01",
    )
    other_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 6743,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
