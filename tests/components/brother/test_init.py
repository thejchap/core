"""Test init of Brother integration."""

from unittest.mock import AsyncMock

from brother import SnmpError
from tryke import Depends, expect, fixture, test

from homeassistant.components.brother.const import (
    CONF_COMMUNITY,
    DOMAIN,
    SECTION_ADVANCED_SETTINGS,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TYPE
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import mock_brother, mock_brother_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def async_setup_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test a successful setup entry."""
    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)


@test
async def config_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test for setup failure if connection to broker is missing."""
    mock_brother_client.async_update.side_effect = ConnectionError

    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("snmp_error", exc=SnmpError("SNMP Error")),
    test.case("connection_error", exc=ConnectionError()),
)
async def error_on_init(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_brother: AsyncMock = Depends(mock_brother),
    _client: AsyncMock = Depends(mock_brother_client),
    *,
    exc: Exception,
) -> None:
    """Test for error on init."""
    mock_brother.create.side_effect = exc

    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_brother_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful unload of entry."""
    await init_integration(hass, mock_config_entry)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
    expect(bool(hass.data.get(DOMAIN))).to_be(False)


@test
async def migrate_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_brother_client),
) -> None:
    """Test entry migration to minor_version=2."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="HL-L2340DW 0123456789",
        unique_id="0123456789",
        data={CONF_HOST: "localhost", CONF_TYPE: "laser"},
        minor_version=1,
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.minor_version).to_equal(2)
    expect(config_entry.data[SECTION_ADVANCED_SETTINGS][CONF_PORT]).to_equal(161)
    expect(config_entry.data[SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY]).to_equal("public")


@test
async def serial_mismatch(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _brother: AsyncMock = Depends(mock_brother),
    mock_brother_client: AsyncMock = Depends(mock_brother_client),
) -> None:
    """Test if the serial number matches on init."""
    mock_brother_client.serial = "DIFFERENT_SERIAL"

    await init_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
