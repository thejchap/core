"""Test the Raspberry Pi integration."""

from collections.abc import Generator
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.hassio import DOMAIN as HASSIO_DOMAIN
from homeassistant.components.raspberry_pi.const import DOMAIN
from homeassistant.components.rpi_power import config_flow as rpi_power_config_flow  # noqa: F401
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, MockModule, mock_integration
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@fixture
def mock_rpi_power() -> Generator[None]:
    """Mock the rpi_power integration."""
    with patch(
        "homeassistant.components.rpi_power.async_setup_entry",
        return_value=True,
    ):
        yield


@test
async def setup_entry(
    hass: HomeAssistant = Depends(hass),
    mock_rpi_power: None = Depends(mock_rpi_power),
) -> None:
    """Test setup of a config entry."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Raspberry Pi",
    )
    config_entry.add_to_hass(hass)
    expect(bool(hass.config_entries.async_entries("rpi_power"))).to_be(False)
    with (
        patch(
            "homeassistant.components.raspberry_pi.get_os_info",
            return_value={"board": "rpi"},
        ) as mock_get_os_info,
        patch("homeassistant.components.rpi_power.config_flow.new_under_voltage"),
    ):
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        expect(result).to_be(True)
        await hass.async_block_till_done()
        expect(len(mock_get_os_info.mock_calls)).to_equal(1)

    expect(len(hass.config_entries.async_entries("rpi_power"))).to_equal(1)


@test
async def setup_entry_no_hassio(
    hass: HomeAssistant = Depends(hass),
    mock_rpi_power: None = Depends(mock_rpi_power),
) -> None:
    """Test setup of a config entry without hassio."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Raspberry Pi",
    )
    config_entry.add_to_hass(hass)
    expect(len(hass.config_entries.async_entries())).to_equal(1)

    with patch("homeassistant.components.raspberry_pi.get_os_info") as mock_get_os_info:
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        expect(result).to_be(False)
        await hass.async_block_till_done()

    expect(len(mock_get_os_info.mock_calls)).to_equal(0)
    expect(len(hass.config_entries.async_entries())).to_equal(0)


@test
async def setup_entry_wrong_board(
    hass: HomeAssistant = Depends(hass),
    mock_rpi_power: None = Depends(mock_rpi_power),
) -> None:
    """Test setup of a config entry with wrong board type."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Raspberry Pi",
    )
    config_entry.add_to_hass(hass)
    expect(len(hass.config_entries.async_entries())).to_equal(1)

    with patch(
        "homeassistant.components.raspberry_pi.get_os_info",
        return_value={"board": "generic-x86-64"},
    ) as mock_get_os_info:
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        expect(result).to_be(False)
        await hass.async_block_till_done()

    expect(len(mock_get_os_info.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries())).to_equal(0)


@test
async def setup_entry_wait_hassio(
    hass: HomeAssistant = Depends(hass),
    mock_rpi_power: None = Depends(mock_rpi_power),
) -> None:
    """Test setup of a config entry when hassio has not fetched os_info."""
    mock_integration(hass, MockModule("hassio"))
    await async_setup_component(hass, HASSIO_DOMAIN, {})

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={},
        title="Raspberry Pi",
    )
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.raspberry_pi.get_os_info",
        return_value=None,
    ) as mock_get_os_info:
        result = await hass.config_entries.async_setup(config_entry.entry_id)
        expect(result).to_be(False)
        await hass.async_block_till_done()

    expect(len(mock_get_os_info.mock_calls)).to_equal(1)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
