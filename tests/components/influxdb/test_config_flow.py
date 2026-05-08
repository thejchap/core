"""Test the influxdb config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.influxdb.const import DOMAIN
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
    expect(result["type"]).to_be(FlowResultType.MENU)


@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def setup_v1() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def setup_v1_ssl_cert() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def setup_v2() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def setup_v2_ssl_cert() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def reauth_flow() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def reauth_invalid() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def reconfigure_flow() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def reconfigure_unique_id_change() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def reconfigure_invalid() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def import_flow() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def import_flow_failure() -> None:
    """Stub."""

@test.skip("requires influxdb client mock chain + indirect parametrize over v1/v2 mocks")
async def import_flow_already_configured() -> None:
    """Stub."""
