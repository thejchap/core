"""Tests for the OpenRGB config flow."""

import socket
from unittest.mock import AsyncMock, MagicMock

from openrgb.utils import OpenRGBDisconnected, SDKVersionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.openrgb.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_openrgb_client, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-local fixture executor anchor."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_openrgb_client),
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
    test.case("ConnectionRefusedError", exception=ConnectionRefusedError(), error_key="cannot_connect"),
    test.case("OpenRGBDisconnected", exception=OpenRGBDisconnected(), error_key="cannot_connect"),
    test.case("TimeoutError", exception=TimeoutError(), error_key="cannot_connect"),
    test.case("socket_gaierror", exception=socket.gaierror(), error_key="cannot_connect"),
    test.case("SDKVersionError", exception=SDKVersionError(), error_key="cannot_connect"),
    test.case("RuntimeError", exception=RuntimeError("Test error"), error_key="unknown"),
)
async def user_flow_errors(
    *,
    exception: Exception,
    error_key: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_openrgb_client),
) -> None:
    """Test user flow with various errors and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    client.client_class_mock.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_NAME: "Test Server", CONF_HOST: "127.0.0.1", CONF_PORT: 6742},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error_key})

    client.client_class_mock.side_effect = None

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_openrgb_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow when device is already configured."""
    config_entry.add_to_hass(hass)

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_openrgb_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow when trying to add duplicate host/port combination."""
    config_entry.add_to_hass(hass)

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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_openrgb_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reconfiguration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

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
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.100")
    expect(config_entry.data[CONF_PORT]).to_equal(6743)


@test.cases(
    test.case("ConnectionRefusedError", exception=ConnectionRefusedError(), error_key="cannot_connect"),
    test.case("OpenRGBDisconnected", exception=OpenRGBDisconnected(), error_key="cannot_connect"),
    test.case("TimeoutError", exception=TimeoutError(), error_key="cannot_connect"),
    test.case("socket_gaierror", exception=socket.gaierror(), error_key="cannot_connect"),
    test.case("SDKVersionError", exception=SDKVersionError(), error_key="cannot_connect"),
    test.case("RuntimeError", exception=RuntimeError("Test error"), error_key="unknown"),
)
async def reconfigure_flow_errors(
    *,
    exception: Exception,
    error_key: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: MagicMock = Depends(mock_openrgb_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow with various errors."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    client.client_class_mock.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 6743},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error_key})

    client.client_class_mock.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "192.168.1.100", CONF_PORT: 6743},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("192.168.1.100")
    expect(config_entry.data[CONF_PORT]).to_equal(6743)


@test
async def reconfigure_flow_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _client: MagicMock = Depends(mock_openrgb_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration flow when new config matches another existing entry."""
    config_entry.add_to_hass(hass)

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

    result = await config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 6743,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
