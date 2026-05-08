"""Test Dynalite __init__."""

from unittest.mock import call, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.dynalite import const as dynalite
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def empty_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test with an empty config."""
    expect(await async_setup_component(hass, dynalite.DOMAIN, {})).to_be(True)
    expect(len(hass.config_entries.flow.async_progress())).to_equal(0)
    expect(len(hass.config_entries.async_entries(dynalite.DOMAIN))).to_equal(0)


@test
async def service_request_area_preset(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test requesting and area preset via service call."""
    entry = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: "1.2.3.4"},
    )
    entry2 = MockConfigEntry(
        domain=dynalite.DOMAIN,
        data={CONF_HOST: "5.6.7.8"},
    )
    entry.add_to_hass(hass)
    entry2.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.dynalite.bridge.DynaliteDevices.async_setup",
            return_value=True,
        ),
        patch(
            "dynalite_devices_lib.dynalite.Dynalite.request_area_preset",
            return_value=True,
        ) as mock_req_area_pres,
    ):
        expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        await hass.services.async_call(
            dynalite.DOMAIN,
            "request_area_preset",
            {"host": "1.2.3.4", "area": 2},
        )
        await hass.async_block_till_done()
        mock_req_area_pres.assert_called_once_with(2, 1)
        mock_req_area_pres.reset_mock()
        await hass.services.async_call(
            dynalite.DOMAIN,
            "request_area_preset",
            {"area": 3},
        )
        await hass.async_block_till_done()
        expect(mock_req_area_pres.mock_calls).to_equal([call(3, 1), call(3, 1)])
        mock_req_area_pres.reset_mock()
        await hass.services.async_call(
            dynalite.DOMAIN,
            "request_area_preset",
            {"host": "5.6.7.8", "area": 4},
        )
        await hass.async_block_till_done()
        mock_req_area_pres.assert_called_once_with(4, 1)
        mock_req_area_pres.reset_mock()
        await hass.services.async_call(
            dynalite.DOMAIN,
            "request_area_preset",
            {"host": "6.5.4.3", "area": 5},
        )
        await hass.async_block_till_done()
        mock_req_area_pres.assert_not_called()


@test.skip("complex test_request_channel_level - skip for now")
async def service_request_channel_level() -> None:
    """Stub."""


@test.skip("complex test_async_setup_entry_failed - skip for now")
async def async_setup_entry_failed() -> None:
    """Stub."""
