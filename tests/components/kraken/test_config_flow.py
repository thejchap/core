"""Tests for the kraken config_flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.kraken.const import CONF_TRACKED_ASSET_PAIRS, DOMAIN
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_call_rate_limit_sleep
from .const import (
    MISSING_PAIR_TRADEABLE_ASSET_PAIR_RESPONSE,
    TICKER_INFORMATION_RESPONSE,
    TRADEABLE_ASSET_PAIR_RESPONSE,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _mn: None = Depends(mock_network),
    _mrl: None = Depends(mock_call_rate_limit_sleep),
) -> None:
    """Trigger the hook executor path."""
    return None


@test
async def config_flow(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we can finish a config flow."""
    with patch(
        "homeassistant.components.kraken.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def already_configured(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test we cannot add a second config flow."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("complex coordinator + sensor state setup")
@test
async def options(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options for Kraken."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_SCAN_INTERVAL: 60,
            CONF_TRACKED_ASSET_PAIRS: [
                "ADA/XBT",
                "ADA/ETH",
                "XBT/EUR",
                "XBT/GBP",
                "XBT/USD",
                "XBT/JPY",
            ],
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.kraken.config_flow.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            return_value=TICKER_INFORMATION_RESPONSE,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(hass.states.get("sensor.xbt_usd_ask")).not_.to_be(None)

        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_SCAN_INTERVAL: 10,
                CONF_TRACKED_ASSET_PAIRS: ["ADA/ETH"],
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        await hass.async_block_till_done()

        ada_eth_sensor = hass.states.get("sensor.ada_eth_ask")
        expect(ada_eth_sensor.state).to_equal("0.0003494")

        expect(hass.states.get("sensor.xbt_usd_ask")).to_be(None)


@test.skip("complex coordinator + sensor state setup")
@test
async def deselect_removed_pair(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Test options for Kraken."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={
            CONF_SCAN_INTERVAL: 60,
            CONF_TRACKED_ASSET_PAIRS: [
                "XBT/USD",
            ],
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.kraken.config_flow.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            return_value=TICKER_INFORMATION_RESPONSE,
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.kraken.config_flow.KrakenAPI.get_tradable_asset_pairs",
            return_value=MISSING_PAIR_TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=MISSING_PAIR_TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            return_value=TICKER_INFORMATION_RESPONSE,
        ),
    ):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        schema = result["data_schema"].schema
        expect("XBT/USD" in schema.get(CONF_TRACKED_ASSET_PAIRS).options).to_be(True)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_SCAN_INTERVAL: 10,
                CONF_TRACKED_ASSET_PAIRS: ["ADA/ETH"],
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        await hass.async_block_till_done()

        ada_eth_sensor = hass.states.get("sensor.ada_eth_ask")
        expect(ada_eth_sensor.state).to_equal("0.0003494")
