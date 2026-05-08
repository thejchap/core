"""Test the Cloudflare integration."""

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
import pycfdns
from tryke import Depends, expect, fixture, test

from homeassistant.components.cloudflare.const import (
    CONF_RECORDS,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    SERVICE_UPDATE_RECORDS,
)
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util.location import LocationInfo

from . import ENTRY_CONFIG, get_mock_client, init_integration

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)


LOCATION_PATCH_TARGET = (
    "homeassistant.components.cloudflare.coordinator.async_detect_location_info"
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def cfupdate() -> Generator[MagicMock]:
    """Mock the CloudflareUpdater for easier testing."""
    mock_cfupdate = get_mock_client()
    with patch(
        "homeassistant.components.cloudflare.coordinator.pycfdns.Client",
        return_value=mock_cfupdate,
    ) as mock_api:
        yield mock_api


@fixture
def location_info() -> Generator[None]:
    """Mock the LocationInfo for easier testing."""
    with patch(
        LOCATION_PATCH_TARGET,
        return_value=LocationInfo(
            "0.0.0.0",
            "US",
            "USD",
            "CA",
            "California",
            "San Diego",
            "92122",
            "America/Los_Angeles",
            32.8594,
            -117.2073,
            True,
        ),
    ):
        yield


@test
async def async_setup_raises_entry_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
) -> None:
    """Test that it throws ConfigEntryNotReady when exception occurs during setup."""
    instance = cfupdate.return_value

    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    instance.list_zones.side_effect = pycfdns.ComunicationException()
    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def async_setup_raises_entry_auth_failed(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
) -> None:
    """Test that it throws ConfigEntryAuthFailed when exception occurs during setup."""
    instance = cfupdate.return_value

    entry = MockConfigEntry(domain=DOMAIN, data=ENTRY_CONFIG)
    entry.add_to_hass(hass)

    instance.list_zones.side_effect = pycfdns.AuthenticationException()
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)

    flow = flows[0]
    expect(flow["step_id"]).to_equal("reauth_confirm")
    expect(flow["handler"]).to_equal(DOMAIN)

    expect("context" in flow).to_be(True)
    expect(flow["context"]["source"]).to_equal(SOURCE_REAUTH)
    expect(flow["context"]["entry_id"]).to_equal(entry.entry_id)


@test
async def unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
    _location: None = Depends(location_info),
) -> None:
    """Test successful unload of entry."""
    entry = await init_integration(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def integration_services(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
    caplog: LogCapture = Depends(caplog_fixture),
    _location: None = Depends(location_info),
) -> None:
    """Test integration services."""
    instance = cfupdate.return_value

    entry = await init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(instance.update_dns_record.mock_calls)).to_equal(2)
    instance.update_dns_record.reset_mock()

    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_RECORDS,
        {},
        blocking=True,
    )
    await hass.async_block_till_done()

    expect(len(instance.update_dns_record.mock_calls)).to_equal(2)
    expect("All target records are up to date" not in caplog.text).to_be(True)


@test
async def integration_services_with_issue(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
    caplog: LogCapture = Depends(caplog_fixture),
    _location: None = Depends(location_info),
) -> None:
    """Test integration services with issue."""
    instance = cfupdate.return_value

    entry = await init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(len(instance.update_dns_record.mock_calls)).to_equal(2)
    instance.update_dns_record.reset_mock()

    with patch(LOCATION_PATCH_TARGET, return_value=None):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPDATE_RECORDS,
            {},
            blocking=True,
        )

    instance.update_dns_record.assert_not_called()
    expect("Could not get external IPv4 address" in caplog.text).to_be(True)


@test
async def integration_services_with_nonexisting_record(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
    caplog: LogCapture = Depends(caplog_fixture),
    _location: None = Depends(location_info),
) -> None:
    """Test integration services."""
    instance = cfupdate.return_value

    entry = await init_integration(
        hass, data={**ENTRY_CONFIG, CONF_RECORDS: ["nonexisting.example.com"]}
    )
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_RECORDS,
        {},
        blocking=True,
    )
    await hass.async_block_till_done()

    instance.update_dns_record.assert_not_called()
    expect("All target records are up to date" in caplog.text).to_be(True)


@test
async def integration_update_interval(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cfupdate: MagicMock = Depends(cfupdate),
    caplog: LogCapture = Depends(caplog_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    _location: None = Depends(location_info),
) -> None:
    """Test integration update interval."""
    instance = cfupdate.return_value

    entry = await init_integration(hass)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    freezer.tick(timedelta(minutes=DEFAULT_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(len(instance.list_dns_records.mock_calls)).to_equal(2)
    expect(len(instance.update_dns_record.mock_calls)).to_equal(4)
    expect("All target records are up to date" not in caplog.text).to_be(True)

    instance.list_dns_records.side_effect = pycfdns.AuthenticationException()
    freezer.tick(timedelta(minutes=DEFAULT_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(len(instance.list_dns_records.mock_calls)).to_equal(3)
    expect(len(instance.update_dns_record.mock_calls)).to_equal(4)

    instance.list_dns_records.side_effect = pycfdns.ComunicationException()
    freezer.tick(timedelta(minutes=DEFAULT_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    expect(len(instance.list_dns_records.mock_calls)).to_equal(4)
    expect(len(instance.update_dns_record.mock_calls)).to_equal(4)
