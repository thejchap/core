"""Test the Broadlink config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.broadlink.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import get_device
from ._fixtures import broadlink_setup, mock_heartbeat

from tests.hass_fixtures import hass as hass_fixture, mock_network

DEVICE_HELLO = "homeassistant.components.broadlink.config_flow.blk.hello"


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
    _heartbeat: None = Depends(mock_heartbeat),
    _setup: None = Depends(broadlink_setup),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def flow_user_works(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a config flow initiated by the user."""
    device = get_device("Living Room")
    mock_api = device.get_mock_api()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(DEVICE_HELLO, return_value=mock_api) as mock_hello:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": device.host, "timeout": device.timeout},
        )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("finish")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": device.name},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(device.name)
    expect(result["data"]).to_equal(device.get_entry_data())

    expect(mock_hello.call_count).to_equal(1)
    expect(mock_api.auth.call_count).to_equal(1)


@test.skip("multiple-flow-progress test not yet ported")
async def flow_user_already_in_progress(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we do not accept more than one config flow per device."""


@test.skip("invalid_host_test not yet ported")
async def flow_user_invalid_host(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test invalid host handling."""


@test.skip("auth flow tests not yet ported")
async def flow_user_authentication(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test auth-related flow."""


@test.skip("device_offline_test not yet ported")
async def flow_user_device_offline(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test device offline handling."""


@test.skip("flow tests with multiple parametrize not yet ported")
async def flow_user_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test already configured."""


@test.skip("dhcp flow tests not yet ported")
async def flow_dhcp_can_finish(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test dhcp flow can finish."""


@test.skip("dhcp flow tests not yet ported")
async def flow_dhcp_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test dhcp flow already configured."""


@test.skip("dhcp flow tests not yet ported")
async def flow_dhcp_unsupported_device(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test dhcp flow unsupported device."""


@test.skip("reauth flow tests not yet ported")
async def flow_reauth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth flow."""
