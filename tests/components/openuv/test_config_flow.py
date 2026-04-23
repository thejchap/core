"""Define tests for the OpenUV config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from pyopenuv.errors import InvalidApiKeyError
from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.components.openuv.const import (
    CONF_FROM_WINDOW,
    CONF_TO_WINDOW,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_ELEVATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    TEST_API_KEY,
    TEST_ELEVATION,
    TEST_LATITUDE,
    TEST_LONGITUDE,
    client as client_fx,
    config as config_fx,
    config_entry as config_entry_fx,
    mock_pyopenuv as mock_pyopenuv_fx,
    mock_setup_entry as mock_setup_entry_fx,
    setup_config_entry as setup_config_entry_fx,
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire mock_network and mock_setup_entry for every test (usefixtures pytestmark)."""


@test
async def create_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(client_fx),
    config: dict[str, Any] = Depends(config_fx),
    _mock_pyopenuv: None = Depends(mock_pyopenuv_fx),
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch.object(client, "uv_index", AsyncMock(side_effect=InvalidApiKeyError)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{TEST_LATITUDE}, {TEST_LONGITUDE}")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: TEST_API_KEY,
            CONF_ELEVATION: TEST_ELEVATION,
            CONF_LATITUDE: TEST_LATITUDE,
            CONF_LONGITUDE: TEST_LONGITUDE,
        }
    )


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test config flow options."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    def get_schema_marker(data_schema: vol.Schema, key: str) -> vol.Marker | None:
        for k in data_schema.schema:
            if k == key and isinstance(k, vol.Marker):
                return k
        return None

    expect(
        get_schema_marker(result["data_schema"], CONF_FROM_WINDOW).description
    ).to_equal({"suggested_value": 3.5})
    expect(
        get_schema_marker(result["data_schema"], CONF_TO_WINDOW).description
    ).to_equal({"suggested_value": 3.5})

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_FROM_WINDOW: 3.5, CONF_TO_WINDOW: 2.0}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({CONF_FROM_WINDOW: 3.5, CONF_TO_WINDOW: 2.0})

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    expect(
        get_schema_marker(result["data_schema"], CONF_FROM_WINDOW).description
    ).to_equal({"suggested_value": 3.5})
    expect(
        get_schema_marker(result["data_schema"], CONF_TO_WINDOW).description
    ).to_equal({"suggested_value": 2.0})


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup: None = Depends(setup_config_entry_fx),
) -> None:
    """Test that the reauth step works."""
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_KEY: "new_api_key"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
