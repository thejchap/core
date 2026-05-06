"""Tryke fixtures for the iqvia integration."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

from tryke import Depends, fixture

from homeassistant.components.iqvia.const import CONF_ZIP_CODE, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.json import JsonObjectType

from tests.common import MockConfigEntry, load_json_object_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
def config() -> dict[str, Any]:
    """Define a config entry data fixture."""
    return {
        CONF_ZIP_CODE: "12345",
    }


@fixture
def config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
) -> MockConfigEntry:
    """Define a config entry fixture."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=config[CONF_ZIP_CODE],
        data=config,
        entry_id="690ac4b7e99855fc5ee7b987a758d5cb",
    )
    entry.add_to_hass(hass)
    return entry


@fixture
def data_allergy_forecast() -> JsonObjectType:
    """Define allergy forecast data."""
    return load_json_object_fixture("allergy_forecast_data.json", "iqvia")


@fixture
def data_allergy_index() -> JsonObjectType:
    """Define allergy index data."""
    return load_json_object_fixture("allergy_index_data.json", "iqvia")


@fixture
def data_allergy_outlook() -> JsonObjectType:
    """Define allergy outlook data."""
    return load_json_object_fixture("allergy_outlook_data.json", "iqvia")


@fixture
def data_asthma_forecast() -> JsonObjectType:
    """Define asthma forecast data."""
    return load_json_object_fixture("asthma_forecast_data.json", "iqvia")


@fixture
def data_asthma_index() -> JsonObjectType:
    """Define asthma index data."""
    return load_json_object_fixture("asthma_index_data.json", "iqvia")


@fixture
def data_disease_forecast() -> JsonObjectType:
    """Define disease forecast data."""
    return load_json_object_fixture("disease_forecast_data.json", "iqvia")


@fixture
def data_disease_index() -> JsonObjectType:
    """Define disease index data."""
    return load_json_object_fixture("disease_index_data.json", "iqvia")


@fixture
async def setup_iqvia(
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config),
    data_allergy_forecast: JsonObjectType = Depends(data_allergy_forecast),
    data_allergy_index: JsonObjectType = Depends(data_allergy_index),
    data_allergy_outlook: JsonObjectType = Depends(data_allergy_outlook),
    data_asthma_forecast: JsonObjectType = Depends(data_asthma_forecast),
    data_asthma_index: JsonObjectType = Depends(data_asthma_index),
    data_disease_forecast: JsonObjectType = Depends(data_disease_forecast),
    data_disease_index: JsonObjectType = Depends(data_disease_index),
) -> AsyncGenerator[None]:
    """Define a fixture to set up IQVIA."""
    with (
        patch(
            "pyiqvia.allergens.Allergens.extended", return_value=data_allergy_forecast
        ),
        patch("pyiqvia.allergens.Allergens.current", return_value=data_allergy_index),
        patch("pyiqvia.allergens.Allergens.outlook", return_value=data_allergy_outlook),
        patch("pyiqvia.asthma.Asthma.extended", return_value=data_asthma_forecast),
        patch("pyiqvia.asthma.Asthma.current", return_value=data_asthma_index),
        patch("pyiqvia.disease.Disease.extended", return_value=data_disease_forecast),
        patch("pyiqvia.disease.Disease.current", return_value=data_disease_index),
        patch("homeassistant.components.iqvia.PLATFORMS", []),
    ):
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()
        yield
