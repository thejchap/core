"""Test the PECO Outage Counter init file."""

from unittest.mock import patch

from peco import (
    AlertResults,
    BadJSONError,
    HttpError,
    OutageResults,
    UnresponsiveMeterError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.peco.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_ENTRY_DATA = {"county": "TOTAL"}
COUNTY_ENTRY_DATA = {"county": "BUCKS"}
INVALID_COUNTY_DATA = {"county": "INVALID"}
METER_DATA = {"county": "BUCKS", "phone_number": "1234567890"}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def unload_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the unload entry."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "peco.PecoOutageApi.get_outage_totals",
            return_value=OutageResults(
                customers_out=0,
                percent_customers_out=0,
                outage_count=0,
                customers_served=350394,
            ),
        ),
        patch(
            "peco.PecoOutageApi.get_map_alerts",
            return_value=AlertResults(
                alert_content="Testing 1234", alert_title="Testing 4321"
            ),
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()
    entries = hass.config_entries.async_entries(DOMAIN)
    expect(len(entries)).to_equal(1)
    expect(entries[0].state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(entries[0].entry_id)
    await hass.async_block_till_done()
    expect(entries[0].state).to_be(ConfigEntryState.NOT_LOADED)


@test.cases(
    test.case("bucks_customers_out", sensor="bucks_customers_out"),
    test.case("bucks_percent_customers_out", sensor="bucks_percent_customers_out"),
    test.case("bucks_outage_count", sensor="bucks_outage_count"),
    test.case("bucks_customers_served", sensor="bucks_customers_served"),
)
async def update_timeout(
    sensor: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when there is a timeout."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=COUNTY_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    with patch(
        "peco.PecoOutageApi.get_outage_count",
        side_effect=TimeoutError(),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get(f"sensor.{sensor}")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("total_customers_out", sensor="total_customers_out"),
    test.case("total_percent_customers_out", sensor="total_percent_customers_out"),
    test.case("total_outage_count", sensor="total_outage_count"),
    test.case("total_customers_served", sensor="total_customers_served"),
)
async def total_update_timeout(
    sensor: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when there is a timeout."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_ENTRY_DATA)
    config_entry.add_to_hass(hass)
    with patch(
        "peco.PecoOutageApi.get_outage_totals",
        side_effect=TimeoutError(),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get(f"sensor.{sensor}")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("bucks_customers_out", sensor="bucks_customers_out"),
    test.case("bucks_percent_customers_out", sensor="bucks_percent_customers_out"),
    test.case("bucks_outage_count", sensor="bucks_outage_count"),
    test.case("bucks_customers_served", sensor="bucks_customers_served"),
)
async def http_error(
    sensor: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when an abnormal status code is returned."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=COUNTY_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    with patch(
        "peco.PecoOutageApi.get_outage_count",
        side_effect=HttpError(),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get(f"sensor.{sensor}")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("bucks_customers_out", sensor="bucks_customers_out"),
    test.case("bucks_percent_customers_out", sensor="bucks_percent_customers_out"),
    test.case("bucks_outage_count", sensor="bucks_outage_count"),
    test.case("bucks_customers_served", sensor="bucks_customers_served"),
)
async def bad_json(
    sensor: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when abnormal JSON is returned."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=COUNTY_ENTRY_DATA)
    config_entry.add_to_hass(hass)

    with patch(
        "peco.PecoOutageApi.get_outage_count",
        side_effect=BadJSONError(),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get(f"sensor.{sensor}")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unresponsive_meter_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when the meter will not respond."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=METER_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "peco.PecoOutageApi.meter_check",
            side_effect=UnresponsiveMeterError(),
        ),
        patch(
            "peco.PecoOutageApi.get_outage_count",
            return_value=OutageResults(
                customers_out=0,
                percent_customers_out=0,
                outage_count=0,
                customers_served=350394,
            ),
        ),
        patch(
            "peco.PecoOutageApi.get_map_alerts",
            return_value=AlertResults(
                alert_content="Testing 1234", alert_title="Testing 4321"
            ),
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.meter_status")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def meter_http_error(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when there is an HTTP error."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=METER_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "peco.PecoOutageApi.meter_check",
            side_effect=HttpError(),
        ),
        patch(
            "peco.PecoOutageApi.get_outage_count",
            return_value=OutageResults(
                customers_out=0,
                percent_customers_out=0,
                outage_count=0,
                customers_served=350394,
            ),
        ),
        patch(
            "peco.PecoOutageApi.get_map_alerts",
            return_value=AlertResults(
                alert_content="Testing 1234", alert_title="Testing 4321"
            ),
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.meter_status")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def meter_bad_json(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when there is bad JSON."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=METER_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "peco.PecoOutageApi.meter_check",
            side_effect=BadJSONError(),
        ),
        patch(
            "peco.PecoOutageApi.get_outage_count",
            return_value=OutageResults(
                customers_out=0,
                percent_customers_out=0,
                outage_count=0,
                customers_served=350394,
            ),
        ),
        patch(
            "peco.PecoOutageApi.get_map_alerts",
            return_value=AlertResults(
                alert_content="Testing 1234", alert_title="Testing 4321"
            ),
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.meter_status")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def meter_timeout(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if it raises an error when there is a timeout."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=METER_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "peco.PecoOutageApi.meter_check",
            side_effect=TimeoutError(),
        ),
        patch(
            "peco.PecoOutageApi.get_outage_count",
            return_value=OutageResults(
                customers_out=0,
                percent_customers_out=0,
                outage_count=0,
                customers_served=350394,
            ),
        ),
        patch(
            "peco.PecoOutageApi.get_map_alerts",
            return_value=AlertResults(
                alert_content="Testing 1234", alert_title="Testing 4321"
            ),
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_falsy()
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.meter_status")).to_be_none()
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def meter_data(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test if the meter returns the value successfully."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=METER_DATA)
    config_entry.add_to_hass(hass)

    with (
        patch(
            "peco.PecoOutageApi.meter_check",
            return_value=True,
        ),
        patch(
            "peco.PecoOutageApi.get_outage_count",
            return_value=OutageResults(
                customers_out=0,
                percent_customers_out=0,
                outage_count=0,
                customers_served=350394,
            ),
        ),
        patch(
            "peco.PecoOutageApi.get_map_alerts",
            return_value=AlertResults(
                alert_content="Testing 1234", alert_title="Testing 4321"
            ),
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
        await hass.async_block_till_done()

    expect(hass.states.get("binary_sensor.meter_status")).not_.to_be_none()
    expect(hass.states.get("binary_sensor.meter_status").state).to_equal("on")
    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
