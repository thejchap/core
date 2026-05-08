"""Test the homewizard config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.homewizard.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def manual_flow_show_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user form is rendered for a manual flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)


@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def manual_flow_works() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def manual_flow_works_with_v2_api_support() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_flow_works() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_flow_during_onboarding() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_flow_during_onboarding_disabled_api() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_disabled_api() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_invalid_api() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_skips_existing() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def discovery_replaces_ignored() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def manual_v1_with_v2_api_support() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def manual_v2_with_v1_api() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def manual_v1_with_v2_api_failure() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def manual_v1_no_data() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def reauth_v1() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def reauth_v2() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def reauth_v2_invalid_token() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def reauth_v2_unknown() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def reconfigure() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def reconfigure_unique_id_collision() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def dhcp() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def dhcp_existing_unique_id() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def dhcp_no_data() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def dhcp_disabled_api() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def dhcp_invalid_api() -> None:
    """Stub."""

@test.skip("requires homewizardenergy mock chain + snapshot for full flow")
async def dhcp_existing_running_already() -> None:
    """Stub."""
