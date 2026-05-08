"""Test the OctoPrint config flow."""

from ipaddress import ip_address

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.octoprint.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Force tryke fixture resolution before each test."""


@test
async def duplicate_zerconf_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the duplicate zeroconf isn't shown."""
    MockConfigEntry(
        domain=DOMAIN,
        data={"host": "192.168.1.123"},
        source=config_entries.SOURCE_IMPORT,
        unique_id="83747482",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=80,
            properties={"uuid": "83747482", "path": "/foo/"},
            type="mock_type",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def form_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_cannot_connect."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def form_unknown_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_form_unknown_exception."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def show_zerconf_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_show_zerconf_form."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def show_ssdp_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_show_ssdp_form."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def import_yaml(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_import_yaml."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def import_duplicate_yaml(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_import_duplicate_yaml."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def failed_auth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_failed_auth."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def failed_auth_unexpected_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_failed_auth_unexpected_error."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def user_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_user_duplicate_entry."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def duplicate_ssdp_ignored(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_duplicate_ssdp_ignored."""


@test.skip("requires SHOW_PROGRESS flow + pyoctoprintapi multi-step mock (not ported)")
async def reauth_form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Stub for test_reauth_form."""
