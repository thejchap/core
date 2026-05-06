"""Tests for Fing config flow."""

import httpx
from tryke import Depends, expect, fixture, test

from homeassistant.components.fing.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    make_mock_config_entry,
    make_mocked_fing_agent,
    mock_config_entry,
    mocked_fing_agent,
)

from tests.common import AsyncMock, MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def verify_connection_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _agent: AsyncMock = Depends(mocked_fing_agent),
) -> None:
    """Test successful connection verification."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_IP_ADDRESS: "192.168.1.1",
            CONF_PORT: "49090",
            CONF_API_KEY: "test_key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(dict(entry.data))

    new_entry = result["result"]
    expect(new_entry.unique_id).to_equal("0000000000XX")
    expect(new_entry.domain).to_equal(DOMAIN)


@test
async def verify_api_version_outdated(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test connection verification failure."""
    # Use api_type="old" by constructing fixtures directly.
    _entry = make_mock_config_entry("old")
    agent_gen = make_mocked_fing_agent("old")
    next(agent_gen)
    try:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_IP_ADDRESS: "192.168.1.1",
                CONF_PORT: "49090",
                CONF_API_KEY: "test_key",
            },
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("api_version_error")
    finally:
        # Trigger generator cleanup (exit the patches).
        for _ in agent_gen:
            pass


@test.cases(
    test.case(
        "network_error",
        exception=httpx.NetworkError("Network error"),
        error="cannot_connect",
    ),
    test.case(
        "timeout",
        exception=httpx.TimeoutException("Timeout error"),
        error="timeout_connect",
    ),
    test.case(
        "http_500",
        exception=httpx.HTTPStatusError(
            "HTTP status error - 500", request=None, response=httpx.Response(500)
        ),
        error="http_status_error",
    ),
    test.case(
        "http_401",
        exception=httpx.HTTPStatusError(
            "HTTP status error - 401", request=None, response=httpx.Response(401)
        ),
        error="invalid_api_key",
    ),
    test.case(
        "http_error",
        exception=httpx.HTTPError("HTTP error"),
        error="unknown",
    ),
    test.case(
        "invalid_url",
        exception=httpx.InvalidURL("Invalid URL"),
        error="url_error",
    ),
    test.case(
        "cookie_conflict",
        exception=httpx.CookieConflict("Cookie conflict"),
        error="unknown",
    ),
    test.case(
        "stream_error",
        exception=httpx.StreamError("Stream error"),
        error="unknown",
    ),
)
async def http_error_handling(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    agent: AsyncMock = Depends(mocked_fing_agent),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test handling of HTTP-related errors during connection verification."""
    agent.get_devices.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_IP_ADDRESS: "192.168.1.1",
            CONF_PORT: "49090",
            CONF_API_KEY: "test_key",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal(error)

    # Simulate a successful connection after the error
    agent.get_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_IP_ADDRESS: "192.168.1.1",
            CONF_PORT: "49090",
            CONF_API_KEY: "test_key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(dict(entry.data))


@test
async def duplicate_entries(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _agent: AsyncMock = Depends(mocked_fing_agent),
) -> None:
    """Test detecting duplicate entries."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_IP_ADDRESS: "192.168.1.1",
            CONF_PORT: "49090",
            CONF_API_KEY: "test_key",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
