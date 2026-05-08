"""Test the Hunter Douglas Powerview scene platform."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.hunterdouglas_powerview.const import DOMAIN
from homeassistant.components.scene import DOMAIN as SCENE_DOMAIN, SERVICE_TURN_ON
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from ._fixtures import hub_patches

from .const import MOCK_MAC

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test.cases(
    test.case("api_v1", api_version=1),
    test.case("api_v2", api_version=2),
    test.case("api_v3", api_version=3),
)
async def scenes(
    *,
    api_version: int,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the scenes."""
    with hub_patches(api_version):
        entry = MockConfigEntry(
            domain=DOMAIN, data={"host": "1.2.3.4"}, unique_id=MOCK_MAC
        )
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        expect(hass.states.async_entity_ids_count(SCENE_DOMAIN)).to_equal(18)

        suffix_names = [
            "close_lounge_room",
            "close_bed_4",
            "close_bed_2",
            "close_master_bed",
            "close_family",
            "open_bed_4",
            "open_master_bed",
            "open_bed_3",
            "open_family",
            "close_study",
            "open_all",
            "close_all",
            "open_kitchen",
            "open_lounge_room",
            "open_bed_2",
            "close_bed_3",
            "close_kitchen",
            "open_study",
        ]
        for suffix in suffix_names:
            entity_id = f"scene.powerview_generation_{api_version}_{suffix}"
            state = hass.states.get(entity_id)
            expect(state).not_.to_be(None)
            expect(state.state).to_equal(STATE_UNKNOWN)

        with patch(
            "homeassistant.components.hunterdouglas_powerview.scene.PvScene.activate"
        ) as mock_activate:
            await hass.services.async_call(
                SCENE_DOMAIN,
                SERVICE_TURN_ON,
                {"entity_id": f"scene.powerview_generation_{api_version}_open_study"},
                blocking=True,
            )
            await hass.async_block_till_done()

        mock_activate.assert_called_once()
