"""Define tests for the Airzone Cloud init."""

from unittest.mock import patch

from aioairzone_cloud.exceptions import AirzoneTimeout
from tryke import Depends, expect, fixture, test

from homeassistant.components.airzone_cloud.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .util import CONFIG

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def unload_entry(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test unload."""
    config_entry = MockConfigEntry(
        data=CONFIG,
        domain=DOMAIN,
        unique_id="airzone_cloud_unique_id",
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.login",
            return_value=None,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.logout",
            return_value=None,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.list_installations",
            return_value=[],
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.update_installation",
            return_value=None,
        ),
        patch(
            "homeassistant.components.airzone_cloud.AirzoneCloudApi.update",
            return_value=None,
        ),
    ):
        expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.LOADED)

        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def init_api_timeout(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test API timeouts when loading the Airzone Cloud integration."""
    with patch(
        "homeassistant.components.airzone_cloud.AirzoneCloudApi.login",
        side_effect=AirzoneTimeout,
    ):
        config_entry = MockConfigEntry(
            data=CONFIG,
            domain=DOMAIN,
            unique_id="airzone_cloud_unique_id",
        )
        config_entry.add_to_hass(hass)

        expect(
            await hass.config_entries.async_setup(config_entry.entry_id)
        ).to_be(False)
