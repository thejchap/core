"""Test the lamarzocco config flow."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.lamarzocco.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import USER_INPUT
from ._fixtures import (
    mock_cloud_client,
    mock_config_entry,
    mock_generate_installation_key,
    mock_lamarzocco,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def form_abort_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: MagicMock = Depends(mock_setup_entry),
    _gen_key: MagicMock = Depends(mock_generate_installation_key),
    _cloud: MagicMock = Depends(mock_cloud_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("machine_selection")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"machine": "GS012345"},
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("port deferred - sibling test")
async def form() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def form_invalid_auth() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def form_no_machines() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def reauth_flow() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def reconfigure_flow() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def reconfigure_flow_no_machines() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bluetooth_discovery() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bluetooth_discovery_already_configured() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def bluetooth_discovery_errors() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def dhcp_discovery() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def dhcp_discovery_already_configured() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def dhcp_discovery_already_configured_full_data() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def options_flow() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def options_flow_offline() -> None:
    """Stub."""
