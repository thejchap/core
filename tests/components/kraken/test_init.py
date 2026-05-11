"""Tests for the kraken integration."""

from unittest.mock import patch

from pykrakenapi.pykrakenapi import CallRateLimitError, KrakenAPIError
from tryke import Depends, expect, fixture, test

from homeassistant.components.kraken.const import DOMAIN
from homeassistant.core import HomeAssistant

from .const import TICKER_INFORMATION_RESPONSE, TRADEABLE_ASSET_PAIR_RESPONSE

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test unload for Kraken."""
    with (
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            return_value=TICKER_INFORMATION_RESPONSE,
        ),
    ):
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
        expect(DOMAIN in hass.data).to_be(False)


@test
async def unknown_error(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test unload for Kraken."""
    with (
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            side_effect=KrakenAPIError("EQuery: Error"),
        ),
    ):
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect("Unable to fetch data from Kraken.com:" in caplog.text).to_be(True)


@test
async def callrate_limit(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test unload for Kraken."""
    with (
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            side_effect=CallRateLimitError(),
        ),
    ):
        entry = MockConfigEntry(domain=DOMAIN)
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        expect(
            "Exceeded the Kraken.com call rate limit. Increase the update interval to"
            " prevent this error" in caplog.text
        ).to_be(True)
