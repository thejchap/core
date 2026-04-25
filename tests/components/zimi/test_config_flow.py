"""Tests for the zimi config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test
from zcc import (
    ControlPointCannotConnectError,
    ControlPointConnectionRefusedError,
    ControlPointDescription,
    ControlPointError,
    ControlPointInvalidHostError,
    ControlPointTimeoutError,
)

from homeassistant import config_entries
from homeassistant.components.zimi.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.device_registry import format_mac

from ._fixtures import discovery_mock, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


INPUT_MAC = "aa:bb:cc:dd:ee:ff"
INPUT_MAC_EXTRA = "aa:bb:cc:dd:ee:ee"
INPUT_HOST = "192.168.1.100"
INPUT_HOST_EXTRA = "192.168.1.101"
INPUT_PORT = 5003
INPUT_PORT_EXTRA = 5004
SELECTED_HOST_AND_PORT = "selected_host_and_port"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def user_discovery_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
) -> None:
    """Test user form transitions to creation if zcc discovery succeeds."""
    discovery.discovers.return_value = [
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT)
    ]
    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["context"]).to_equal(
        {"source": config_entries.SOURCE_USER, "unique_id": INPUT_MAC}
    )
    expect(result["data"]).to_equal(
        {"host": INPUT_HOST, "port": INPUT_PORT, "mac": format_mac(INPUT_MAC)}
    )


@test
async def user_discovery_success_selection(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
) -> None:
    """Test user form transitions via selection to creation if discovery has multiple hosts."""
    discovery.discovers.return_value = [
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT),
        ControlPointDescription(host=INPUT_HOST_EXTRA, port=INPUT_PORT_EXTRA),
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("selection")
    expect(result["errors"]).to_equal({})

    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(
            host=INPUT_HOST_EXTRA, port=INPUT_PORT_EXTRA, mac=INPUT_MAC_EXTRA
        )
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {SELECTED_HOST_AND_PORT: f"{INPUT_HOST_EXTRA}:{INPUT_PORT_EXTRA!s}"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {"host": INPUT_HOST_EXTRA, "port": INPUT_PORT_EXTRA, "mac": format_mac(INPUT_MAC_EXTRA)}
    )


@test
async def user_discovery_duplicates(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
) -> None:
    """Test that flow is aborted if duplicates are added."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id=INPUT_MAC,
        data={
            CONF_HOST: INPUT_HOST,
            CONF_PORT: INPUT_PORT,
            "mac": format_mac(INPUT_MAC),
        },
    ).add_to_hass(hass)

    discovery.discovers.return_value = [
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT)
    ]
    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def finish_manual_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
) -> None:
    """Test manual form transitions to creation with valid data."""
    discovery.discovers.side_effect = ControlPointError("Discovery failed")
    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"ZIMI Controller ({INPUT_HOST}:{INPUT_PORT})")
    expect(result["data"]).to_equal(
        {"host": INPUT_HOST, "port": INPUT_PORT, "mac": format_mac(INPUT_MAC)}
    )


@test
async def manual_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
) -> None:
    """Test manual form transitions via cannot_connect to creation."""
    discovery.discovers.side_effect = ControlPointError("Discovery failed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal({})

    discovery.return_value.validate_connection.side_effect = (
        ControlPointCannotConnectError
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    discovery.return_value.validate_connection.side_effect = None
    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"ZIMI Controller ({INPUT_HOST}:{INPUT_PORT})")
    expect(result["data"]).to_equal(
        {"host": INPUT_HOST, "port": INPUT_PORT, "mac": format_mac(INPUT_MAC)}
    )


@test
async def manual_gethostbyname_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
) -> None:
    """Test manual form transitions via gethostbyname failure to creation."""
    discovery.discovers.side_effect = ControlPointError("Discovery failed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal({})

    discovery.return_value.validate_connection.side_effect = (
        ControlPointInvalidHostError
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["step_id"])).to_be(True)
    expect(result["errors"]).to_equal({"base": "invalid_host"})

    discovery.return_value.validate_connection.side_effect = None
    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"ZIMI Controller ({INPUT_HOST}:{INPUT_PORT})")
    expect(result["data"]).to_equal(
        {"host": INPUT_HOST, "port": INPUT_PORT, "mac": format_mac(INPUT_MAC)}
    )


@test.cases(
    test.case("invalid_host", side_effect=ControlPointInvalidHostError, error_expected={"base": "invalid_host"}),
    test.case("connection_refused", side_effect=ControlPointConnectionRefusedError, error_expected={"base": "connection_refused"}),
    test.case("cannot_connect", side_effect=ControlPointCannotConnectError, error_expected={"base": "cannot_connect"}),
    test.case("timeout", side_effect=ControlPointTimeoutError, error_expected={"base": "timeout"}),
    test.case("unknown", side_effect=Exception, error_expected={"base": "unknown"}),
)
async def manual_connection_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    discovery: MagicMock = Depends(discovery_mock),
    *,
    side_effect: type[Exception],
    error_expected: dict,
) -> None:
    """Test manual form connection errors."""
    discovery.discovers.side_effect = ControlPointError("Discovery failed")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal({})

    discovery.return_value.validate_connection.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("manual")
    expect(result["errors"]).to_equal(error_expected)

    discovery.return_value.validate_connection.side_effect = None
    discovery.return_value.validate_connection.return_value = (
        ControlPointDescription(host=INPUT_HOST, port=INPUT_PORT, mac=INPUT_MAC)
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: INPUT_HOST, CONF_PORT: INPUT_PORT},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"ZIMI Controller ({INPUT_HOST}:{INPUT_PORT})")
    expect(result["data"]).to_equal(
        {"host": INPUT_HOST, "port": INPUT_PORT, "mac": format_mac(INPUT_MAC)}
    )
