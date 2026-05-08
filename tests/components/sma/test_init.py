"""Test the sma init file."""

from unittest.mock import MagicMock

from pysma import SmaAuthenticationException, SmaConnectionException, SmaReadException
from tryke import Depends, expect, fixture, test

from homeassistant.components.sma.const import DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntryState
from homeassistant.core import HomeAssistant

from . import MOCK_DEVICE, MOCK_USER_INPUT, setup_integration
from ._fixtures import mock_config_entry, mock_sma_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def migrate_entry_minor_version_1_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _entry: MockConfigEntry = Depends(mock_config_entry),
    _sma: MagicMock = Depends(mock_sma_client),
) -> None:
    """Test migrating a 1.1 config entry to 1.2."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_DEVICE.name,
        unique_id=MOCK_DEVICE.serial,
        data=MOCK_USER_INPUT,
        source=SOURCE_IMPORT,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    expect(entry.version).to_equal(1)
    expect(entry.minor_version).to_equal(2)
    expect(isinstance(MOCK_DEVICE.serial, str)).to_be(True)
    expect(entry.unique_id).to_equal(MOCK_DEVICE.serial)


@test.cases(
    test.case(
        "connection_exception",
        exception=SmaConnectionException,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
    test.case(
        "auth_exception",
        exception=SmaAuthenticationException,
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "read_exception",
        exception=SmaReadException,
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_exceptions(
    exception: type[Exception],
    expected_state: ConfigEntryState,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    sma: MagicMock = Depends(mock_sma_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the _async_setup."""
    sma.device_info.side_effect = exception
    await setup_integration(hass, config_entry)
    expect(config_entry.state).to_equal(expected_state)
