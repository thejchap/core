"""Define tests for the Freedompro config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.freedompro.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.components.freedompro._fixtures import mock_freedompro, mock_setup_entry
from tests.components.freedompro.const import DEVICES
from tests.hass_fixtures import hass as hass_fixture, mock_network

VALID_CONFIG = {
    CONF_API_KEY: "ksdjfgslkjdfksjdfksjgfksjd",
}


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
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    _mock_freedompro: None = Depends(mock_freedompro),
    _mn: None = Depends(mock_network),
    _mz: MagicMock = Depends(_mock_zeroconf),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def show_form(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the form is served with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")


@test
async def invalid_auth(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that errors are shown when API key is invalid."""
    with patch(
        "homeassistant.components.freedompro.config_flow.get_list",
        return_value={
            "state": False,
            "code": -201,
        },
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=VALID_CONFIG,
        )

        expect(result["errors"]).to_equal({"base": "invalid_auth"})


@test
async def connection_error(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that errors are shown when API key is invalid."""
    with patch(
        "homeassistant.components.freedompro.config_flow.get_list",
        return_value={
            "state": False,
            "code": -200,
        },
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=VALID_CONFIG,
        )

        expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def create_entry(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test that the user step works."""
    with patch(
        "homeassistant.components.freedompro.config_flow.get_list",
        return_value={
            "state": True,
            "devices": DEVICES,
        },
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=VALID_CONFIG,
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("Freedompro")
        expect(result["data"][CONF_API_KEY]).to_equal("ksdjfgslkjdfksjdfksjgfksjd")
