"""Test the enphase_envoy config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.enphase_envoy.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def show_user_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form is shown for an empty flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})


@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def form() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def user_no_serial_number() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def user_fetching_serial_fails() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def form_invalid_auth() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def form_cannot_connect() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def form_unknown_error() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def zeroconf() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def zeroconf_pre_token_firmware() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def zero_conf_old_blank_entry() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def zero_conf_old_blank_entry_standard_title() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def zero_conf_existing_unique_id() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def zero_conf_new_envoy() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def reauth() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def reconfigure() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def reconfigure_unique_id_collision() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def options_flow() -> None:
    """Stub."""

@test.skip("requires pyenphase Envoy mock chain (auth, token, model, parametrize)")
async def options_default() -> None:
    """Stub."""
