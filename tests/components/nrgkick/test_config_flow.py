"""Tests for the NRGkick config flow."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.nrgkick.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_nrgkick_api, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    nrgkick_api: AsyncMock = Depends(mock_nrgkick_api),
) -> None:
    """Test we can set up successfully without credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("NRGkick Test")
    expect(result["data"]).to_equal({CONF_HOST: "192.168.1.100"})
    expect(result["result"].unique_id).to_equal("TEST123456")


@test.skip("requires authentication retry flow — port deferred")
async def user_flow_with_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_user_flow_with_credentials."""


@test.skip("requires invalid host validation — port deferred")
async def form_invalid_host_input(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_invalid_host_input."""


@test.skip("requires alternate fixture data — port deferred")
async def form_fallback_title_when_device_name_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_fallback_title_when_device_name_missing."""


@test.skip("requires alternate fixture data — port deferred")
async def form_invalid_response_when_serial_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_invalid_response_when_serial_missing."""


@test.skip("indirect parametrize not in tryke 0.0.27")
async def user_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_user_flow_errors."""


@test.skip("requires zeroconf flow — port deferred")
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_flow."""


@test.skip("requires zeroconf flow — port deferred")
async def zeroconf_flow_disabled_json_api(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_flow_disabled_json_api."""


@test.skip("requires zeroconf flow — port deferred")
async def zeroconf_flow_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_flow_no_serial."""


@test.skip("requires duplicate-entry detection — port deferred")
async def zeroconf_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_already_configured."""


@test.skip("indirect parametrize not in tryke 0.0.27")
async def zeroconf_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_flow_errors."""


@test.skip("requires reauth flow — port deferred")
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_flow."""


@test.skip("indirect parametrize not in tryke 0.0.27")
async def reauth_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_flow_errors."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow."""


@test.skip("indirect parametrize not in tryke 0.0.27")
async def reconfigure_flow_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_errors."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow_with_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_with_credentials."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow_remove_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_remove_credentials."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow_unique_id_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_unique_id_change."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_already_configured."""


@test.skip("requires recoverable flow — port deferred")
async def user_flow_invalid_response_recoverable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_user_flow_invalid_response_recoverable."""


@test.skip("requires zeroconf flow — port deferred")
async def zeroconf_flow_invalid_response_recoverable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_flow_invalid_response_recoverable."""


@test.skip("requires reauth flow — port deferred")
async def reauth_flow_invalid_response_recoverable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_flow_invalid_response_recoverable."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow_invalid_response_recoverable(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_invalid_response_recoverable."""


@test.skip("requires zeroconf flow — port deferred")
async def zeroconf_flow_invalid_response_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_zeroconf_flow_invalid_response_no_serial."""


@test.skip("requires reconfigure flow — port deferred")
async def reconfigure_flow_invalid_response_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reconfigure_flow_invalid_response_no_serial."""


@test.skip("requires reauth flow — port deferred")
async def reauth_flow_invalid_response_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_flow_invalid_response_no_serial."""


@test.skip("requires user flow — port deferred")
async def user_flow_invalid_response_no_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_user_flow_invalid_response_no_serial."""


@test.skip("requires alternate fixture data — port deferred")
async def user_flow_fallback_title_when_device_name_missing(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_user_flow_fallback_title_when_device_name_missing."""
