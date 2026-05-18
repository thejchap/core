"""The tests for the siren component."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.siren import (
    SirenEntity,
    SirenEntityDescription,
    process_turn_on_params,
)
from homeassistant.components.siren.const import SirenEntityFeature
from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass, mock_network


@fixture
def _trigger_executor(_network=Depends(mock_network)) -> int:
    return 0


class MockSirenEntity(SirenEntity):
    """Mock siren device to use in tests."""

    _attr_is_on = True

    def __init__(
        self,
        supported_features=0,
        available_tones_as_attr=None,
        available_tones_in_desc=None,
    ) -> None:
        """Initialize mock siren entity."""
        self._attr_supported_features = supported_features
        if available_tones_as_attr is not None:
            self._attr_available_tones = available_tones_as_attr
        elif available_tones_in_desc is not None:
            self.entity_description = SirenEntityDescription(
                "mock", available_tones=available_tones_in_desc
            )


@test
async def sync_turn_on(hass: HomeAssistant = Depends(hass)) -> None:
    """Test if async turn_on calls sync turn_on."""
    siren = MockSirenEntity()
    siren.hass = hass

    siren.turn_on = MagicMock()
    await siren.async_turn_on()

    expect(siren.turn_on.called).to_be_truthy()


@test
async def sync_turn_off(hass: HomeAssistant = Depends(hass)) -> None:
    """Test if async turn_off calls sync turn_off."""
    siren = MockSirenEntity()
    siren.hass = hass

    siren.turn_off = MagicMock()
    await siren.async_turn_off()

    expect(siren.turn_off.called).to_be_truthy()


@test
async def no_available_tones(hass: HomeAssistant = Depends(hass)) -> None:
    """Test ValueError when siren advertises tones but has no available_tones."""
    siren = MockSirenEntity(SirenEntityFeature.TONES)
    siren.hass = hass
    expect(lambda: process_turn_on_params(siren, {"tone": "test"})).to_raise(ValueError)


@test
async def available_tones_list(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that valid tones from tone list will get passed in."""
    siren = MockSirenEntity(
        SirenEntityFeature.TONES, available_tones_as_attr=["a", "b"]
    )
    siren.hass = hass
    expect(process_turn_on_params(siren, {"tone": "a"})).to_equal({"tone": "a"})


@test
async def available_tones(hass: HomeAssistant = Depends(hass)) -> None:
    """Test different available tones scenarios."""
    siren = MockSirenEntity(
        SirenEntityFeature.TONES, available_tones_in_desc=["a", "b"]
    )
    expect(siren.available_tones).to_equal(["a", "b"])
    siren = MockSirenEntity(SirenEntityFeature.TONES)
    expect(siren.available_tones).to_be_none()


@test
async def available_tones_dict(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that valid tones from available_tones dict will get passed in."""
    siren = MockSirenEntity(SirenEntityFeature.TONES, {1: "a", 2: "b"})
    siren.hass = hass
    expect(process_turn_on_params(siren, {"tone": "a"})).to_equal({"tone": 1})
    expect(process_turn_on_params(siren, {"tone": 1})).to_equal({"tone": 1})


@test
async def missing_tones_list(hass: HomeAssistant = Depends(hass)) -> None:
    """Test ValueError when setting a tone that is missing from available_tones list."""
    siren = MockSirenEntity(SirenEntityFeature.TONES, ["a", "b"])
    siren.hass = hass
    expect(lambda: process_turn_on_params(siren, {"tone": "test"})).to_raise(ValueError)


@test
async def missing_tones_dict(hass: HomeAssistant = Depends(hass)) -> None:
    """Test ValueError when setting a tone that is missing from available_tones dict."""
    siren = MockSirenEntity(SirenEntityFeature.TONES, {1: "a", 2: "b"})
    siren.hass = hass
    expect(lambda: process_turn_on_params(siren, {"tone": 3})).to_raise(ValueError)
