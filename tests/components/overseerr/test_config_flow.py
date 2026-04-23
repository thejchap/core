"""Tests for the Overseerr config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from python_overseerr.exceptions import (
    OverseerrAuthenticationError,
    OverseerrConnectionError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.overseerr.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    CONF_URL,
    CONF_WEBHOOK_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import WEBHOOK_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_overseerr_client as mock_overseerr_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
    patch_webhook_id as patch_webhook_id_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _webhook: None = Depends(patch_webhook_id_fx),
) -> None:
    """Wire mock_network and webhook patch for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr.test", CONF_API_KEY: "test-key"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Seerr")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "overseerr.test",
            CONF_PORT: 80,
            CONF_SSL: False,
            CONF_API_KEY: "test-key",
            CONF_WEBHOOK_ID: "test-webhook-id",
        }
    )


@test.cases(
    test.case("invalid_auth", OverseerrAuthenticationError, "invalid_auth"),
    test.case("cannot_connect", OverseerrConnectionError, "cannot_connect"),
)
async def flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test flow errors."""
    mock_overseerr_client.get_request_count.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr.test", CONF_API_KEY: "test-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_overseerr_client.get_request_count.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr.test", CONF_API_KEY: "test-key"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def flow_invalid_host(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test flow invalid host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://", CONF_API_KEY: "test-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"url": "invalid_host"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr.test", CONF_API_KEY: "test-key"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test duplicate flow."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr.test", CONF_API_KEY: "test-key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "new-test-key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new-test-key")


@test.cases(
    test.case("invalid_auth", OverseerrAuthenticationError, "invalid_auth"),
    test.case("cannot_connect", OverseerrConnectionError, "cannot_connect"),
)
async def reauth_flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reauth flow errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_overseerr_client.get_request_count.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "new-test-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_overseerr_client.get_request_count.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "new-test-key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(mock_config_entry.data[CONF_API_KEY]).to_equal("new-test-key")


@test
async def reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr2.test", CONF_API_KEY: "new-key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_HOST: "overseerr2.test",
            CONF_PORT: 80,
            CONF_SSL: False,
            CONF_API_KEY: "new-key",
            CONF_WEBHOOK_ID: WEBHOOK_ID,
        }
    )


@test.cases(
    test.case("invalid_auth", OverseerrAuthenticationError, "invalid_auth"),
    test.case("cannot_connect", OverseerrConnectionError, "cannot_connect"),
)
async def reconfigure_flow_errors(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_overseerr_client: AsyncMock = Depends(mock_overseerr_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure flow errors."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    mock_overseerr_client.get_request_count.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr2.test", CONF_API_KEY: "new-key"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_overseerr_client.get_request_count.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_URL: "http://overseerr2.test", CONF_API_KEY: "new-key"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
