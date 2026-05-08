"""Test the epson init."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.epson.const import CONF_CONNECTION_TYPE, DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def migrate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test successful migration of entry data from version 1 to 1.2."""

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Epson",
        version=1,
        minor_version=1,
        data={CONF_HOST: "1.1.1.1"},
        entry_id="1cb78c095906279574a0442a1f0003ef",
    )
    expect(mock_entry.version).to_equal(1)

    mock_entry.add_to_hass(hass)

    with patch("homeassistant.components.epson.Projector.get_power"):
        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

    expect(mock_entry).not_.to_be(None)
    expect(mock_entry.version).to_equal(1)
    expect(mock_entry.minor_version).to_equal(2)
    expect(mock_entry.data.get(CONF_CONNECTION_TYPE)).to_equal("http")
    expect(mock_entry.data.get(CONF_HOST)).to_equal("1.1.1.1")
