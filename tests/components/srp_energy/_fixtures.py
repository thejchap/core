"""Tryke fixtures for SRP Energy integration tests."""

from __future__ import annotations

from collections.abc import Generator
import datetime as dt
from unittest.mock import MagicMock, patch

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, fixture

from homeassistant.components.srp_energy.const import DOMAIN, PHOENIX_TIME_ZONE
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from . import MOCK_USAGE, TEST_CONFIG_HOME

from tests.common import MockConfigEntry
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture


@fixture
async def setup_hass_config(hass: HomeAssistant = Depends(hass_fixture)) -> None:
    """Configure the home assistant core for SRP tests."""
    hass.config.latitude = 33.27
    hass.config.longitude = 112
    await hass.config.async_set_time_zone(PHOENIX_TIME_ZONE)


@fixture
def hass_tz_info(
    hass: HomeAssistant = Depends(hass_fixture),
    _cfg: None = Depends(setup_hass_config),
) -> dt.tzinfo | None:
    """Return timezone info for the hass timezone."""
    return dt_util.get_time_zone(hass.config.time_zone)


@fixture
def test_date(
    tz: dt.tzinfo | None = Depends(hass_tz_info),
) -> dt.datetime:
    """Return test datetime for the hass timezone."""
    return dt.datetime(2022, 8, 2, 0, 0, 0, 0, tzinfo=tz)


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN, data=TEST_CONFIG_HOME, unique_id=TEST_CONFIG_HOME[CONF_ID]
    )


@fixture
def mock_srp_energy() -> Generator[MagicMock]:
    """Return a mocked SrpEnergyClient client."""
    with patch(
        "homeassistant.components.srp_energy.SrpEnergyClient", autospec=True
    ) as srp_energy_mock:
        client = srp_energy_mock.return_value
        client.validate.return_value = True
        client.usage.return_value = MOCK_USAGE
        yield client


@fixture
def mock_srp_energy_config_flow() -> Generator[MagicMock]:
    """Return a mocked config_flow SrpEnergyClient client."""
    with patch(
        "homeassistant.components.srp_energy.config_flow.SrpEnergyClient",
        autospec=True,
    ) as srp_energy_mock:
        client = srp_energy_mock.return_value
        client.validate.return_value = True
        client.usage.return_value = MOCK_USAGE
        yield client


@fixture
def mock_setup_entry() -> Generator[MagicMock]:
    """Mock async_setup_entry."""
    with patch(
        "homeassistant.components.srp_energy.async_setup_entry", return_value=True
    ) as mock:
        yield mock


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
    date: dt.datetime = Depends(test_date),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_srp_energy),
    _client_flow: MagicMock = Depends(mock_srp_energy_config_flow),
) -> MockConfigEntry:
    """Set up the Srp Energy integration for testing."""
    freezer.move_to(date)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry
