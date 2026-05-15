"""Test ESPHome enum mapper."""

from enum import StrEnum

from aioesphomeapi import APIIntEnum
from tryke import expect, test

from homeassistant.components.esphome.enum_mapper import EsphomeEnumMapper


class MockEnum(APIIntEnum):
    """Mock enum."""

    ESPHOME_FOO = 1
    ESPHOME_BAR = 2


class MockStrEnum(StrEnum):
    """Mock enum."""

    HA_FOO = "foo"
    HA_BAR = "bar"


MOCK_MAPPING: EsphomeEnumMapper[MockEnum, MockStrEnum] = EsphomeEnumMapper(
    {
        MockEnum.ESPHOME_FOO: MockStrEnum.HA_FOO,
        MockEnum.ESPHOME_BAR: MockStrEnum.HA_BAR,
    }
)


@test
async def map_esphome_to_ha() -> None:
    """Test mapping from ESPHome to HA."""
    expect(MOCK_MAPPING.from_esphome(MockEnum.ESPHOME_FOO)).to_equal(MockStrEnum.HA_FOO)
    expect(MOCK_MAPPING.from_esphome(MockEnum.ESPHOME_BAR)).to_equal(MockStrEnum.HA_BAR)


@test
async def map_ha_to_esphome() -> None:
    """Test mapping from HA to ESPHome."""
    expect(MOCK_MAPPING.from_hass(MockStrEnum.HA_FOO)).to_equal(MockEnum.ESPHOME_FOO)
    expect(MOCK_MAPPING.from_hass(MockStrEnum.HA_BAR)).to_equal(MockEnum.ESPHOME_BAR)
