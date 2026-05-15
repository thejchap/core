"""Tryke fixtures for rainforest_eagle tests."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from tryke import Depends, fixture


_RAINFOREST_TRANSLATIONS = {
    "component.rainforest_eagle.entity.sensor.energy_price.name": "Energy price",
    "component.rainforest_eagle.entity.sensor.power_demand.name": "Power demand",
    "component.rainforest_eagle.entity.sensor.total_energy_delivered.name": (
        "Total energy delivered"
    ),
    "component.rainforest_eagle.entity.sensor.total_energy_received.name": (
        "Total energy received"
    ),
}


async def _fake_get_translations(
    hass, language, category, integrations=None, config_flow=None
):
    return _RAINFOREST_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _RAINFOREST_TRANSLATIONS


@fixture
def rainforest_translations() -> Generator[None]:
    """Inject rainforest_eagle translations so entity slugs include translation_key names."""
    with (
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        yield

from homeassistant.components.rainforest_eagle.const import (
    CONF_CLOUD_ID,
    CONF_HARDWARE_ADDRESS,
    CONF_INSTALL_CODE,
    DOMAIN,
    TYPE_EAGLE_100,
    TYPE_EAGLE_200,
)
from homeassistant.const import CONF_HOST, CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import MOCK_200_RESPONSE_WITHOUT_PRICE, MOCK_CLOUD_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def config_entry_200(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Return a config entry."""
    entry = MockConfigEntry(
        domain="rainforest_eagle",
        data={
            CONF_CLOUD_ID: MOCK_CLOUD_ID,
            CONF_HOST: "192.168.1.55",
            CONF_INSTALL_CODE: "abcdefgh",
            CONF_HARDWARE_ADDRESS: "mock-hw-address",
            CONF_TYPE: TYPE_EAGLE_200,
        },
    )
    entry.add_to_hass(hass)
    return entry


@fixture
async def setup_rainforest_200(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_200),
) -> AsyncGenerator[Mock]:
    """Set up rainforest."""
    with patch(
        "aioeagle.ElectricMeter.create_instance",
        return_value=Mock(
            get_device_query=AsyncMock(return_value=MOCK_200_RESPONSE_WITHOUT_PRICE)
        ),
    ) as mock_update:
        mock_update.return_value.is_connected = True
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        yield mock_update.return_value


@fixture
async def setup_rainforest_100(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[MagicMock]:
    """Set up rainforest."""
    MockConfigEntry(
        domain="rainforest_eagle",
        data={
            CONF_CLOUD_ID: MOCK_CLOUD_ID,
            CONF_HOST: "192.168.1.55",
            CONF_INSTALL_CODE: "abcdefgh",
            CONF_HARDWARE_ADDRESS: None,
            CONF_TYPE: TYPE_EAGLE_100,
        },
    ).add_to_hass(hass)
    with patch(
        "homeassistant.components.rainforest_eagle.coordinator.Eagle100Reader",
        return_value=Mock(
            get_instantaneous_demand=Mock(
                return_value={"InstantaneousDemand": {"Demand": "1.152000"}}
            ),
            get_current_summation=Mock(
                return_value={
                    "CurrentSummation": {
                        "SummationDelivered": "45251.285000",
                        "SummationReceived": "232.232000",
                    }
                }
            ),
        ),
    ) as mock_update:
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
        yield mock_update
