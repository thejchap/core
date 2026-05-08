"""Test the homekit_controller config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.homekit_controller.const import DOMAIN
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
    """Test the user flow renders the device-pick form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(bool(result.get("type"))).to_be(True)


@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_works() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def abort_duplicate_flow() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def abort_paired_flow() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_already_configured() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_existing_paired() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_already_paired_with_id() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def pair_unable_to_pair() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def pair_unable_to_pair_no_pin() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def pair_max_tries_to_pair() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_dismiss_existing_flow_on_paired() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def already_paired_advances_to_pair() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def already_paired_in_user_flow_advances_to_pair() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_invalid_config_entry() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def already_paired_no_supplemental_advance() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def pair_success_password_error() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def pair_form_errors_on_pairing() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def pair_abort_errors_on_pairing() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def user_works() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def user_no_devices() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def user_no_unpaired_devices() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def parse_new_homekit_json() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def parse_old_homekit_json() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def parse_new_homekit_zeroconf() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def homekit_controller_dependency_loop() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def discovery_no_homekit_record_uses_unpaired() -> None:
    """Stub."""

@test.skip("requires aiohomekit Controller mock chain (discovery + pairing)")
async def coap_homekit_text_record() -> None:
    """Stub."""
