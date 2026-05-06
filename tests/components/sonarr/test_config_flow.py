"""Test the Sonarr config flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aiopyarr import ArrAuthenticationException, ArrException
from tryke import Depends, expect, fixture, test

from homeassistant.components.sonarr.const import (
    CONF_UPCOMING_DAYS,
    CONF_WANTED_MAX_ITEMS,
    DEFAULT_UPCOMING_DAYS,
    DEFAULT_WANTED_MAX_ITEMS,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_SOURCE, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import MOCK_REAUTH_INPUT, MOCK_USER_INPUT
from ._fixtures import (
    init_integration,
    mock_setup_entry,
    mock_sonarr_config_flow,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    expect(result["step_id"]).to_equal("user")
    expect(result["type"]).to_be(FlowResultType.FORM)


@test
async def cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_sonarr_config_flow),
) -> None:
    """Test we show user form on connection error."""
    client.async_get_system_status.side_effect = ArrException

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def url_rewrite(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_sonarr_config_flow),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = MOCK_USER_INPUT.copy()
    user_input[CONF_URL] = "https://192.168.1.189"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("192.168.1.189")
    expect(result["data"][CONF_URL]).to_equal("https://192.168.1.189:443/")


@test
async def invalid_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_sonarr_config_flow),
) -> None:
    """Test we show user form on invalid auth."""
    client.async_get_system_status.side_effect = ArrAuthenticationException

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def unknown_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(mock_sonarr_config_flow),
) -> None:
    """Test we show user form on unknown error."""
    client.async_get_system_status.side_effect = Exception

    user_input = MOCK_USER_INPUT.copy()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=user_input
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("unknown")


@test
async def full_reauth_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_sonarr_config_flow),
    _setup: None = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test the manual reauth flow from start to finish."""
    result = await entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = MOCK_REAUTH_INPUT.copy()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(entry.data[CONF_API_KEY]).to_equal("test-api-key-reauth")


@test
async def full_user_flow_implementation(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_sonarr_config_flow),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = MOCK_USER_INPUT.copy()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("192.168.1.189")
    expect(result["data"][CONF_URL]).to_equal("http://192.168.1.189:8989/")


@test
async def full_user_flow_advanced_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: MagicMock = Depends(mock_sonarr_config_flow),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Test the full manual user flow with advanced options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER, "show_advanced_options": True}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    user_input = {**MOCK_USER_INPUT, CONF_VERIFY_SSL: True}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("192.168.1.189")
    expect(result["data"][CONF_URL]).to_equal("http://192.168.1.189:8989/")
    expect(result["data"][CONF_VERIFY_SSL]).to_be(True)


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(mock_setup_entry),
    entry: MockConfigEntry = Depends(init_integration),
) -> None:
    """Test updating options."""
    with patch("homeassistant.components.sonarr.PLATFORMS", []):
        expect(entry.options[CONF_UPCOMING_DAYS]).to_equal(DEFAULT_UPCOMING_DAYS)
        expect(entry.options[CONF_WANTED_MAX_ITEMS]).to_equal(
            DEFAULT_WANTED_MAX_ITEMS
        )

        result = await hass.config_entries.options.async_init(entry.entry_id)

        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("init")

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_UPCOMING_DAYS: 2, CONF_WANTED_MAX_ITEMS: 100},
        )
        await hass.async_block_till_done()

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["data"][CONF_UPCOMING_DAYS]).to_equal(2)
        expect(result["data"][CONF_WANTED_MAX_ITEMS]).to_equal(100)
