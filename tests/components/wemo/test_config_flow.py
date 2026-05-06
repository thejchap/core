"""Tests for Wemo config flow."""

from dataclasses import asdict

from tryke import Depends, expect, fixture, test

from homeassistant.components.wemo.const import DOMAIN
from homeassistant.components.wemo.coordinator import Options
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import pywemo_discovery_responder

from tests.common import MockConfigEntry, patch
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _responder: None = Depends(pywemo_discovery_responder),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def not_discovered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up with no devices discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    with patch("homeassistant.components.wemo.config_flow.pywemo") as mock_pywemo:
        mock_pywemo.discover_devices.return_value = []
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options."""
    options = Options(enable_subscription=False, enable_long_press=False)
    entry = MockConfigEntry(domain=DOMAIN, title="Wemo")
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=asdict(options)
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(Options(**result["data"])).to_equal(options)


@test
async def invalid_options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test invalid option combinations."""
    entry = MockConfigEntry(domain=DOMAIN, title="Wemo")
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    # enable_subscription must be True if enable_long_press is True (default).
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"enable_subscription": False}
    )
    expect(result["errors"]).to_equal(
        {"enable_subscription": "long_press_requires_subscription"}
    )
