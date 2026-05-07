"""Test the WiZ Platform config flow."""

from unittest.mock import patch

from pywizlight.exceptions import WizLightConnectionError, WizLightTimeOutError
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.wiz.const import DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    FAKE_IP,
    TEST_CONNECTION,
    TEST_SYSTEM_INFO,
    _patch_wizlight,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture to force tryke to resolve dependencies."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    with (
        _patch_wizlight(),
        patch(
            "homeassistant.components.wiz.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.wiz.async_setup", return_value=True
        ) as mock_setup,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["title"]).to_equal("WiZ Dimmable White ABCABC")
    expect(result2["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def user_flow_enters_dns_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we reject dns names and want ips."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "ip.only"},
    )
    await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": "no_ip"})

    with (
        _patch_wizlight(),
        patch(
            "homeassistant.components.wiz.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.wiz.async_setup", return_value=True
        ) as mock_setup,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            TEST_CONNECTION,
        )
        await hass.async_block_till_done()

    expect(result3["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result3["title"]).to_equal("WiZ Dimmable White ABCABC")
    expect(result3["data"]).to_equal(
        {
            CONF_HOST: "1.1.1.1",
        }
    )
    expect(len(mock_setup.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("wiz_timeout", side_effect=WizLightTimeOutError, error_base="bulb_time_out"),
    test.case("wiz_connection", side_effect=WizLightConnectionError, error_base="no_wiz_light"),
    test.case("unknown_exception", side_effect=Exception, error_base="unknown"),
    test.case("connection_refused", side_effect=ConnectionRefusedError, error_base="cannot_connect"),
)
async def user_form_exceptions(
    *,
    side_effect: type[BaseException],
    error_base: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test all user exceptions in the flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.wiz.wizlight.getBulbConfig",
        side_effect=side_effect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )

    expect(result2["type"]).to_be(FlowResultType.FORM)
    expect(result2["errors"]).to_equal({"base": error_base})


@test
async def form_updates_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test a duplicate id aborts and updates existing entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_SYSTEM_INFO["id"],
        data={CONF_HOST: "dummy"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with _patch_wizlight():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            TEST_CONNECTION,
        )
        await hass.async_block_till_done()

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")
    expect(entry.data[CONF_HOST]).to_equal(FAKE_IP)


@test.skip("indirect parametrize over (source, data) tuples; needs port")
async def discovered_by_dhcp_connection_fails() -> None:
    """Test we abort on connection failure."""


@test.skip("indirect parametrize over (source, data) tuples; needs port")
async def discovered_by_dhcp_or_integration_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("indirect parametrize over (source, data) tuples; needs port")
async def discovered_by_dhcp_or_integration_discovery_updates_host() -> None:
    """Skipped pending fixture port."""


@test.skip("indirect parametrize over (source, data) tuples; needs port")
async def discovered_by_dhcp_or_integration_discovery_avoid_waiting_for_retry() -> None:
    """Skipped pending fixture port."""


@test.skip("uses async_setup_integration helper + parametrize")
async def setup_via_discovery() -> None:
    """Skipped pending fixture port."""


@test.skip("uses async_setup_integration helper")
async def setup_via_discovery_cannot_connect() -> None:
    """Skipped pending fixture port."""


@test.skip("uses async_setup_integration helper")
async def setup_via_discovery_exception_finds_nothing() -> None:
    """Skipped pending fixture port."""


@test.skip("uses async_setup_integration helper")
async def discovery_with_firmware_update() -> None:
    """Skipped pending fixture port."""


@test.skip("indirect parametrize")
async def discovered_during_onboarding() -> None:
    """Skipped pending fixture port."""


@test.skip("uses async_setup_integration helper")
async def flow_replace_ignored_device() -> None:
    """Skipped pending fixture port."""
