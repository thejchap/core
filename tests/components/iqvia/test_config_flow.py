"""Define tests for the IQVIA config flow."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.iqvia.const import CONF_ZIP_CODE, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.iqvia._fixtures import config, config_entry, setup_iqvia
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _mock_zeroconf() -> MagicMock:
    """Patch zeroconf so tests don't require a real zeroconf instance."""
    from zeroconf import DNSCache

    with (
        patch("homeassistant.components.zeroconf.HaZeroconf") as mock_zc,
        patch("homeassistant.components.zeroconf.discovery.AsyncServiceBrowser"),
    ):
        zc = mock_zc.return_value
        zc.async_add_service_listener = AsyncMock()
        zc.async_remove_service_listener = AsyncMock()
        zc.async_register_service = AsyncMock()
        zc.async_update_service = AsyncMock()
        zc.cache = DNSCache()
        yield mock_zc


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def duplicate_error(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
    _config_entry: object = Depends(config_entry),
) -> None:
    """Test that errors are shown when duplicates are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def invalid_zip_code(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that an invalid ZIP code key throws an error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_ZIP_CODE: "bad"}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({CONF_ZIP_CODE: "invalid_zip_code"})


@test
async def show_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def step_user(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
    _setup: None = Depends(setup_iqvia),
) -> None:
    """Test that the user step works (without MFA)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("12345")
    expect(result["data"]).to_equal({CONF_ZIP_CODE: "12345"})
