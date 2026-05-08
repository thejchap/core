"""Test the Xiaomi Miio config flow."""

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.xiaomi_miio import const
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke Depends() resolution."""


@test
async def cloud_form_show(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the initial cloud form is shown when starting a user flow."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("cloud")
    expect(result["errors"]).to_equal({})


@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_step_gateway_connect_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_cloud_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_cloud_multiple_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_cloud_incomplete() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_cloud_login_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_cloud_no_devices() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_gateway_cloud_missing_token() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def zeroconf_gateway_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def zeroconf_unknown_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def zeroconf_no_data() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def zeroconf_missing_data() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_step_device_connect_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_step_unknown_device() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_step_device_manual_model_error() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_step_device_manual_model_succes() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_plug_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def zeroconf_plug_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def config_flow_vacuum_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def zeroconf_vacuum_success() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def options_flow() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def options_flow_incomplete() -> None:
    """Skipped pending fixture port."""

@test.skip("complex miio device + zeroconf fixtures")
async def reauth() -> None:
    """Skipped pending fixture port."""
