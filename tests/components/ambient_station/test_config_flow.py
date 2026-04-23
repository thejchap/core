"""Define tests for the Ambient PWS config flow."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from aioambient.errors import AmbientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.ambient_station.const import CONF_APP_KEY, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.ambient_station._fixtures import (
    api,
    config,
    config_entry,
    data_devices,
    mock_aioambient,
    setup_config_entry,
)
from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case(
        "invalid_key",
        AsyncMock(side_effect=AmbientError),
        {"base": "invalid_key"},
    ),
    test.case(
        "no_devices",
        AsyncMock(return_value=[]),
        {"base": "no_devices"},
    ),
)
async def create_entry(
    devices_response: AsyncMock,
    errors: dict[str, str],
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    api: Mock = Depends(api),
    config: dict[str, Any] = Depends(config),
    _mock_aioambient: None = Depends(mock_aioambient),
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"] is FlowResultType.FORM).to_be(True)
    expect(result["step_id"]).to_equal("user")

    with patch.object(api, "get_devices", devices_response):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        expect(result["type"] is FlowResultType.FORM).to_be(True)
        expect(result["errors"]).to_equal(errors)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    expect(result["type"] is FlowResultType.CREATE_ENTRY).to_be(True)
    expect(result["title"]).to_equal("67890fghij67")
    expect(result["data"]).to_equal(
        {
            CONF_API_KEY: "12345abcde12345abcde",
            CONF_APP_KEY: "67890fghij67890fghij",
        }
    )


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    config: dict[str, Any] = Depends(config),
    _config_entry: MockConfigEntry = Depends(config_entry),
    _setup_config_entry: None = Depends(setup_config_entry),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    expect(result["type"] is FlowResultType.ABORT).to_be(True)
    expect(result["reason"]).to_equal("already_configured")
