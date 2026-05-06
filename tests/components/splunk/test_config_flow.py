"""Test the Splunk config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.splunk.const import DEFAULT_HOST, DEFAULT_PORT, DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SSL,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_hass_splunk, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_splunk: AsyncMock = Depends(mock_hass_splunk),
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: True,
            CONF_NAME: "Test Splunk",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("splunk.example.com:8088")
    expect(result["data"]).to_equal(
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: True,
            CONF_VERIFY_SSL: True,
            CONF_NAME: "Test Splunk",
        }
    )

    expect(mock_splunk.check.call_count).to_equal(2)


@test.cases(
    test.case("cannot_connect", side_effect=[False, True], error="cannot_connect"),
    test.case("invalid_auth", side_effect=[True, False], error="invalid_auth"),
    test.case(
        "unknown", side_effect=Exception("Unexpected error"), error="unknown"
    ),
)
async def user_flow_error_and_recovery(
    side_effect: list[bool] | Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_splunk: AsyncMock = Depends(mock_hass_splunk),
) -> None:
    """Test user flow errors and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_splunk.check.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    mock_splunk.check.side_effect = None
    mock_splunk.check.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _splunk: AsyncMock = Depends(mock_hass_splunk),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test user flow when entry is already configured (single instance)."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def import_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _splunk: AsyncMock = Depends(mock_hass_splunk),
) -> None:
    """Test successful import flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
            CONF_NAME: "Imported Splunk",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("splunk.example.com:8088")
    expect(result["data"]).to_equal(
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
            CONF_NAME: "Imported Splunk",
        }
    )


@test.cases(
    test.case("cannot_connect", side_effect=[False, True], reason="cannot_connect"),
    test.case("invalid_auth", side_effect=[True, False], reason="invalid_auth"),
    test.case(
        "unknown", side_effect=Exception("Unexpected error"), reason="unknown"
    ),
)
async def import_flow_error_and_recovery(
    side_effect: list[bool] | Exception,
    reason: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_splunk: AsyncMock = Depends(mock_hass_splunk),
) -> None:
    """Test import flow errors and recovery."""
    mock_splunk.check.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)

    mock_splunk.check.side_effect = None
    mock_splunk.check.return_value = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def import_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _splunk: AsyncMock = Depends(mock_hass_splunk),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test import flow when entry is already configured (single instance)."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_TOKEN: "test-token-123",
            CONF_HOST: DEFAULT_HOST,
            CONF_PORT: DEFAULT_PORT,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def reconfigure_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _splunk: AsyncMock = Depends(mock_hass_splunk),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful reconfigure flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "new-token-456",
            CONF_HOST: "new-splunk.example.com",
            CONF_PORT: 9088,
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
            CONF_NAME: "Updated Splunk",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(entry.data[CONF_HOST]).to_equal("new-splunk.example.com")
    expect(entry.data[CONF_PORT]).to_equal(9088)
    expect(entry.data[CONF_TOKEN]).to_equal("new-token-456")
    expect(entry.data[CONF_SSL]).to_be(True)
    expect(entry.data[CONF_VERIFY_SSL]).to_be(False)
    expect(entry.data[CONF_NAME]).to_equal("Updated Splunk")
    expect(entry.title).to_equal("new-splunk.example.com:9088")


@test.cases(
    test.case("cannot_connect", side_effect=[False, True], error="cannot_connect"),
    test.case("invalid_auth", side_effect=[True, False], error="invalid_auth"),
    test.case(
        "unknown", side_effect=Exception("Unexpected error"), error="unknown"
    ),
)
async def reconfigure_flow_error_and_recovery(
    side_effect: list[bool] | Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_splunk: AsyncMock = Depends(mock_hass_splunk),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfigure flow errors and recovery."""
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)

    mock_splunk.check.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "new-splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reconfigure")
    expect(result["errors"]).to_equal({"base": error})

    mock_splunk.check.side_effect = None
    mock_splunk.check.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "test-token-123",
            CONF_HOST: "new-splunk.example.com",
            CONF_PORT: 8088,
            CONF_SSL: False,
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")


@test
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _splunk: AsyncMock = Depends(mock_hass_splunk),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful reauth flow."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "new-token-456"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_TOKEN]).to_equal("new-token-456")


@test
async def reauth_flow_invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_splunk: AsyncMock = Depends(mock_hass_splunk),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with invalid token and recovery."""
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    mock_splunk.check.side_effect = [True, False]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "invalid-token"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    mock_splunk.check.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "new-valid-token"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_TOKEN]).to_equal("new-valid-token")
