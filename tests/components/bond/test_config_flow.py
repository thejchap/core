"""Test the Bond config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.bond.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import (
    patch_bond_bridge,
    patch_bond_device,
    patch_bond_device_ids,
    patch_bond_device_properties,
    patch_bond_device_state,
    patch_bond_version,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


def _patch_async_setup_entry():
    return patch(
        "homeassistant.components.bond.async_setup_entry",
        return_value=True,
    )


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def user_form(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the user initiated form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        patch_bond_version(return_value={"bondid": "ZXXX12345"}),
        patch_bond_device_ids(return_value=["f6776c11", "f6776c12"]),
        patch_bond_bridge(),
        patch_bond_device_properties(),
        patch_bond_device(),
        patch_bond_device_state(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("bond-name")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "some host",
            CONF_ACCESS_TOKEN: "test-token",
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.skip("zeroconf flow not yet ported")
async def user_form_can_create_when_already_discovered(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we get the user initiated form can create when already discovered."""


@test.skip("zeroconf flow not yet ported")
async def user_form_invalid_auth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle invalid auth."""


@test.skip("zeroconf flow not yet ported")
async def user_form_cannot_connect(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle cannot connect."""


@test.skip("zeroconf flow not yet ported")
async def user_form_old_firmware(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle old firmware."""


@test.skip("zeroconf flow not yet ported")
async def user_form_unexpected_client_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle unexpected client error."""


@test.skip("zeroconf flow not yet ported")
async def user_form_unexpected_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we handle unexpected error."""


@test.skip("zeroconf flow not yet ported")
async def user_form_one_entry_per_device_allowed(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that we abort if there is already an entry for a device."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_form(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we get the zeroconf initiated form."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_form_token_unavailable(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test zeroconf form with token unavailable."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_form_token_times_out(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test zeroconf form with token times out."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_form_with_token_available(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test zeroconf form with token available."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_form_with_token_available_name_unavailable(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test zeroconf form with token available, name unavailable."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test starting a flow from discovery when already configured."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_in_setup_flow_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test starting a flow from discovery when already configured."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_already_configured_refresh_token(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test starting a flow from zeroconf and refresh tokens."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_already_configured_no_reload_same_host(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test starting a flow from zeroconf with same host doesn't reload."""


@test.skip("zeroconf flow not yet ported")
async def zeroconf_form_unexpected_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test zeroconf form with unexpected error."""


@test.skip("dhcp flow not yet ported")
async def dhcp_discovery(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test starting a flow from DHCP discovery."""


@test.skip("dhcp flow not yet ported")
async def dhcp_discovery_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test starting a flow from DHCP discovery already configured."""
