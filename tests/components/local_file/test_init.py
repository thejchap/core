"""Test Statistics component setup process."""

from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.local_file.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import get_config, loaded_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def unload_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    loaded_entry: MockConfigEntry = Depends(loaded_entry),
) -> None:
    """Test unload an entry."""
    expect(loaded_entry.state).to_be(ConfigEntryState.LOADED)
    expect(await hass.config_entries.async_unload(loaded_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(loaded_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def file_not_readable_during_startup(
    hass: HomeAssistant = Depends(_trigger_executor),
    get_config: dict[str, str] = Depends(get_config),
) -> None:
    """Test a warning is shown setup when file is not readable."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        options=get_config,
        entry_id="1",
    )
    config_entry.add_to_hass(hass)

    with (
        patch("os.path.isfile", Mock(return_value=True)),
        patch("os.access", Mock(return_value=False)),
        patch(
            "homeassistant.components.local_file.camera.mimetypes.guess_type",
            Mock(return_value=(None, None)),
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
