"""Tests for the Paperless-ngx config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pypaperless.exceptions import (
    InitializationError,
    PaperlessConnectionError,
    PaperlessForbiddenError,
    PaperlessInactiveOrDeletedError,
    PaperlessInvalidTokenError,
)
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.paperless_ngx.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import USER_INPUT_ONE, USER_INPUT_REAUTH, USER_INPUT_TWO

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_paperless as mock_paperless_fx,
    mock_setup_entry as mock_setup_entry_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: AsyncMock = Depends(mock_async_zeroconf_fx),
    _paperless: AsyncMock = Depends(mock_paperless_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire auto-applied fixtures for every test."""


@test
async def full_config_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test registering an integration and finishing flow works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(bool(result["flow_id"])).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT_ONE,
    )

    config_entry = result["result"]
    expect(config_entry.title).to_equal(USER_INPUT_ONE[CONF_URL])
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.data).to_equal(USER_INPUT_ONE)


@test
async def full_reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reauth flow."""
    mock_config_entry.add_to_hass(hass)

    reauth_flow = await mock_config_entry.start_reauth_flow(hass)
    expect(reauth_flow["type"]).to_be(FlowResultType.FORM)
    expect(reauth_flow["step_id"]).to_equal("reauth_confirm")

    result_configure = await hass.config_entries.flow.async_configure(
        reauth_flow["flow_id"], USER_INPUT_REAUTH
    )

    expect(result_configure["type"]).to_be(FlowResultType.ABORT)
    expect(result_configure["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data[CONF_API_KEY]).to_equal(USER_INPUT_REAUTH[CONF_API_KEY])


@test
async def full_reconfigure_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    reconfigure_flow = await mock_config_entry.start_reconfigure_flow(hass)
    expect(reconfigure_flow["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_flow["step_id"]).to_equal("reconfigure")

    result_configure = await hass.config_entries.flow.async_configure(
        reconfigure_flow["flow_id"],
        USER_INPUT_TWO,
    )

    expect(result_configure["type"]).to_be(FlowResultType.ABORT)
    expect(result_configure["reason"]).to_equal("reconfigure_successful")
    expect(mock_config_entry.data).to_equal(USER_INPUT_TWO)


@test.cases(
    test.case("connection", PaperlessConnectionError(), {CONF_URL: "cannot_connect"}),
    test.case("invalid_token", PaperlessInvalidTokenError(), {CONF_API_KEY: "invalid_api_key"}),
    test.case(
        "inactive_or_deleted",
        PaperlessInactiveOrDeletedError(),
        {CONF_API_KEY: "user_inactive_or_deleted"},
    ),
    test.case("forbidden", PaperlessForbiddenError(), {CONF_API_KEY: "forbidden"}),
    test.case("initialization", InitializationError(), {CONF_URL: "cannot_connect"}),
    test.case("unknown", Exception("BOOM!"), {"base": "unknown"}),
)
async def config_flow_error_handling(
    side_effect: Exception,
    expected_error: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_paperless: AsyncMock = Depends(mock_paperless_fx),
) -> None:
    """Test user step shows correct error for various init issues."""
    mock_paperless.initialize.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=USER_INPUT_ONE,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal(expected_error)

    mock_paperless.initialize.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_ONE,
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(USER_INPUT_ONE[CONF_URL])
    expect(result["data"]).to_equal(USER_INPUT_ONE)


@test.cases(
    test.case("connection", PaperlessConnectionError(), {CONF_URL: "cannot_connect"}),
    test.case("invalid_token", PaperlessInvalidTokenError(), {CONF_API_KEY: "invalid_api_key"}),
    test.case(
        "inactive_or_deleted",
        PaperlessInactiveOrDeletedError(),
        {CONF_API_KEY: "user_inactive_or_deleted"},
    ),
    test.case("forbidden", PaperlessForbiddenError(), {CONF_API_KEY: "forbidden"}),
    test.case("initialization", InitializationError(), {CONF_URL: "cannot_connect"}),
    test.case("unknown", Exception("BOOM!"), {"base": "unknown"}),
)
async def reauth_flow_error_handling(
    side_effect: Exception,
    expected_error: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_paperless: AsyncMock = Depends(mock_paperless_fx),
) -> None:
    """Test reauth flow with various initialization errors."""
    mock_config_entry.add_to_hass(hass)
    mock_paperless.initialize.side_effect = side_effect

    reauth_flow = await mock_config_entry.start_reauth_flow(hass)
    expect(reauth_flow["type"]).to_be(FlowResultType.FORM)
    expect(reauth_flow["step_id"]).to_equal("reauth_confirm")

    result_configure = await hass.config_entries.flow.async_configure(
        reauth_flow["flow_id"], USER_INPUT_REAUTH
    )

    await hass.async_block_till_done()

    expect(result_configure["type"]).to_be(FlowResultType.FORM)
    expect(result_configure["errors"]).to_equal(expected_error)


@test.cases(
    test.case("connection", PaperlessConnectionError(), {CONF_URL: "cannot_connect"}),
    test.case("invalid_token", PaperlessInvalidTokenError(), {CONF_API_KEY: "invalid_api_key"}),
    test.case(
        "inactive_or_deleted",
        PaperlessInactiveOrDeletedError(),
        {CONF_API_KEY: "user_inactive_or_deleted"},
    ),
    test.case("forbidden", PaperlessForbiddenError(), {CONF_API_KEY: "forbidden"}),
    test.case("initialization", InitializationError(), {CONF_URL: "cannot_connect"}),
    test.case("unknown", Exception("BOOM!"), {"base": "unknown"}),
)
async def reconfigure_flow_error_handling(
    side_effect: Exception,
    expected_error: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_paperless: AsyncMock = Depends(mock_paperless_fx),
) -> None:
    """Test reconfigure flow with various initialization errors."""
    mock_config_entry.add_to_hass(hass)
    mock_paperless.initialize.side_effect = side_effect

    reauth_flow = await mock_config_entry.start_reconfigure_flow(hass)
    expect(reauth_flow["type"]).to_be(FlowResultType.FORM)
    expect(reauth_flow["step_id"]).to_equal("reconfigure")

    result_configure = await hass.config_entries.flow.async_configure(
        reauth_flow["flow_id"],
        USER_INPUT_TWO,
    )

    await hass.async_block_till_done()

    expect(result_configure["type"]).to_be(FlowResultType.FORM)
    expect(result_configure["errors"]).to_equal(expected_error)


@test
async def config_already_exists(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test single config flow restriction."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=USER_INPUT_ONE,
        context={"source": config_entries.SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def config_already_exists_reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test reconfigure conflict with another entry."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_two = MockConfigEntry(
        entry_id="J87G00V55WEVTJ0CJHM0GADBH5",
        title="Paperless-ngx - Two",
        domain=DOMAIN,
        data=USER_INPUT_TWO,
    )
    mock_config_entry_two.add_to_hass(hass)

    reconfigure_flow = await mock_config_entry_two.start_reconfigure_flow(hass)
    expect(reconfigure_flow["type"]).to_be(FlowResultType.FORM)
    expect(reconfigure_flow["step_id"]).to_equal("reconfigure")

    result_configure = await hass.config_entries.flow.async_configure(
        reconfigure_flow["flow_id"],
        USER_INPUT_ONE,
    )

    expect(result_configure["type"]).to_be(FlowResultType.ABORT)
    expect(result_configure["reason"]).to_equal("already_configured")
