"""Test the Bond config flow."""

from ipaddress import ip_address
from typing import Any
from unittest.mock import Mock, patch

from aiohttp import ClientConnectionError, ClientResponseError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.bond.const import DOMAIN
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .common import (
    patch_bond_bridge,
    patch_bond_device,
    patch_bond_device_ids,
    patch_bond_device_properties,
    patch_bond_device_state,
    patch_bond_token,
    patch_bond_version,
)

from tests.common import MockConfigEntry
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


@test
async def user_form_invalid_auth(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch_bond_version(return_value={"bond_id": "ZXXX12345"}),
        patch_bond_bridge(),
        patch_bond_device_ids(
            side_effect=ClientResponseError(Mock(), Mock(), status=401),
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "invalid_auth"})


@test
async def user_form_cannot_connect(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle cannot connect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch_bond_version(side_effect=ClientConnectionError()),
        patch_bond_bridge(),
        patch_bond_device_ids(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_form_old_firmware(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle old firmware."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch_bond_version(return_value={"no_bond_id": "present"}),
        patch_bond_bridge(),
        patch_bond_device_ids(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "old_firmware"})


async def _help_test_form_unexpected_error(
    hass: HomeAssistant,
    *,
    source: str,
    initial_input: dict[str, Any] | None = None,
    user_input: dict[str, Any],
    error: Exception,
) -> None:
    with patch_bond_token():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": source}, data=initial_input
        )

    with (
        patch_bond_version(return_value={"bond_id": "ZXXX12345"}),
        patch_bond_device_ids(side_effect=error),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "unknown"})


@test
async def user_form_unexpected_client_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected client error."""
    await _help_test_form_unexpected_error(
        hass,
        source=config_entries.SOURCE_USER,
        user_input={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        error=ClientResponseError(Mock(), Mock(), status=500),
    )


@test
async def user_form_unexpected_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we handle unexpected error."""
    await _help_test_form_unexpected_error(
        hass,
        source=config_entries.SOURCE_USER,
        user_input={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        error=Exception(),
    )


@test
async def user_form_one_entry_per_device_allowed(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that we abort if there is already an entry for a device."""
    MockConfigEntry(
        domain=DOMAIN,
        unique_id="already-registered-bond-id",
        data={CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch_bond_version(return_value={"bondid": "already-registered-bond-id"}),
        patch_bond_bridge(),
        patch_bond_device_ids(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def zeroconf_form(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the zeroconf initiated discovery form."""
    with patch_bond_version(), patch_bond_token():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("127.0.0.1"),
                ip_addresses=[ip_address("127.0.0.1")],
                hostname="mock_hostname",
                name="ZXXX12345.some-other-tail-info",
                port=None,
                properties={},
                type="mock_type",
            ),
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({})

    with (
        patch_bond_version(return_value={"bondid": "ZXXX12345"}),
        patch_bond_bridge(),
        patch_bond_device_ids(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCESS_TOKEN: "test-token"},
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("bond-name")
    expect(result2["data"]).to_equal(
        {CONF_HOST: "127.0.0.1", CONF_ACCESS_TOKEN: "test-token"}
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_already_configured(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test starting a zeroconf flow when already configured aborts and updates host."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="already-registered-bond-id",
        data={CONF_HOST: "stored-host", CONF_ACCESS_TOKEN: "test-token"},
    )
    entry.add_to_hass(hass)

    with _patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("127.0.0.2"),
                ip_addresses=[ip_address("127.0.0.2")],
                hostname="mock_hostname",
                name="already-registered-bond-id.some-other-tail-info",
                port=None,
                properties={},
                type="mock_type",
            ),
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(entry.data["host"]).to_equal("127.0.0.2")
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


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
