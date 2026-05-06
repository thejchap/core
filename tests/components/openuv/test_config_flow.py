"""Define tests for the OpenUV config flow."""

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
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    TEST_API_KEY,
    TEST_ELEVATION,
    TEST_LATITUDE,
    TEST_LONGITUDE,
    client,
    config,
    config_entry,
    data_protection_window,
    data_uv_index,
    mock_pyopenuv,
    mock_setup_entry,
    set_time_zone,
    setup_config_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _setup: AsyncMock = Depends(mock_setup_entry),
    _network: None = Depends(mock_network),
) -> None:
    """Module-level fixture priming common mocks."""


@test
async def create_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_obj: Mock = Depends(client),
    cfg: dict[str, Any] = Depends(config),
    _pyopenuv: None = Depends(mock_pyopenuv),
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    with patch.object(client_obj, "uv_index", AsyncMock(side_effect=InvalidApiKeyError)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=cfg
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal("user")
        expect(result["errors"]).to_equal({CONF_API_KEY: "invalid_api_key"})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=cfg
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(f"{TEST_LATITUDE}, {TEST_LONGITUDE}")
    expect(result["data"]).to_equal(cfg)


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfg: dict[str, Any] = Depends(config),
    _entry: MockConfigEntry = Depends(config_entry),
    _setup_entry: None = Depends(setup_config_entry),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=cfg
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(config_entry),
    _setup_entry: None = Depends(setup_config_entry),
) -> None:
    """Test config flow options."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
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
    expect(entry.options).to_equal({CONF_FROM_WINDOW: 3.5, CONF_TO_WINDOW: 2.0})

    result = await hass.config_entries.options.async_init(entry.entry_id)
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
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _cfg: dict[str, Any] = Depends(config),
    entry: MockConfigEntry = Depends(config_entry),
    _setup_entry: None = Depends(setup_config_entry),
) -> None:
    """Test that the reauth step works."""
    result = await entry.start_reauth_flow(hass)
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
