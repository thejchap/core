"""Test power stat validation."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.energy import validate
from homeassistant.components.energy.data import EnergyManager
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant

from tests.components.energy._fixtures import (
    mock_energy_manager as mock_energy_manager_fx,
    mock_get_metadata as mock_get_metadata_fx,
    mock_is_entity_recorded as mock_is_entity_recorded_fx,
)
from tests.hass_fixtures import hass as hass_fx, mock_network

POWER_UNITS_STRING = ", ".join(tuple(UnitOfPower))


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
    return 0


@test
async def validation_grid_power_valid(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with valid power sensor."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.grid_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )
    hass.states.async_set(
        "sensor.grid_power",
        "1.5",
        {
            "device_class": "power",
            "unit_of_measurement": UnitOfPower.KILO_WATT,
            "state_class": "measurement",
        },
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [[]],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_wrong_unit(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with power sensor having wrong unit."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.grid_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )
    hass.states.async_set(
        "sensor.grid_power",
        "1.5",
        {
            "device_class": "power",
            "unit_of_measurement": "beers",
            "state_class": "measurement",
        },
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "entity_unexpected_unit_power",
                        "affected_entities": {("sensor.grid_power", "beers")},
                        "translation_placeholders": {
                            "power_units": POWER_UNITS_STRING
                        },
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_wrong_state_class(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with power sensor having wrong state class."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.grid_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )
    hass.states.async_set(
        "sensor.grid_power",
        "1.5",
        {
            "device_class": "power",
            "unit_of_measurement": UnitOfPower.KILO_WATT,
            "state_class": "total_increasing",
        },
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "entity_unexpected_state_class",
                        "affected_entities": {
                            ("sensor.grid_power", "total_increasing")
                        },
                        "translation_placeholders": None,
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_entity_missing(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
) -> None:
    """Test validating grid with missing power sensor."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.missing_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "statistics_not_defined",
                        "affected_entities": {("sensor.missing_power", None)},
                        "translation_placeholders": None,
                    },
                    {
                        "type": "entity_not_defined",
                        "affected_entities": {("sensor.missing_power", None)},
                        "translation_placeholders": None,
                    },
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_entity_unavailable(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with unavailable power sensor."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.unavailable_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )
    hass.states.async_set("sensor.unavailable_power", "unavailable", {})

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "entity_unavailable",
                        "affected_entities": {
                            ("sensor.unavailable_power", "unavailable")
                        },
                        "translation_placeholders": None,
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_entity_non_numeric(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with non-numeric power sensor."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.non_numeric_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )
    hass.states.async_set(
        "sensor.non_numeric_power",
        "not_a_number",
        {
            "device_class": "power",
            "unit_of_measurement": UnitOfPower.KILO_WATT,
            "state_class": "measurement",
        },
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "entity_state_non_numeric",
                        "affected_entities": {
                            ("sensor.non_numeric_power", "not_a_number")
                        },
                        "translation_placeholders": None,
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_wrong_device_class(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with power sensor having wrong device class."""
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.wrong_device_class_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )
    hass.states.async_set(
        "sensor.wrong_device_class_power",
        "1.5",
        {
            "device_class": "energy",
            "unit_of_measurement": "kWh",
            "state_class": "measurement",
        },
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "entity_unexpected_device_class",
                        "affected_entities": {
                            ("sensor.wrong_device_class_power", "energy")
                        },
                        "translation_placeholders": None,
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_different_units(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with power sensors using different valid units."""
    # With unified format, each grid has one power sensor, so we use two grids
    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.power_watt",
                    "cost_adjustment_day": 0.0,
                },
                {
                    "type": "grid",
                    "stat_rate": "sensor.power_milliwatt",
                    "cost_adjustment_day": 0.0,
                },
            ]
        }
    )
    hass.states.async_set(
        "sensor.power_watt",
        "1500",
        {
            "device_class": "power",
            "unit_of_measurement": UnitOfPower.WATT,
            "state_class": "measurement",
        },
    )
    hass.states.async_set(
        "sensor.power_milliwatt",
        "1500000",
        {
            "device_class": "power",
            "unit_of_measurement": UnitOfPower.MILLIWATT,
            "state_class": "measurement",
        },
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [[], []],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_external_statistics(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with external power statistics (non-entity)."""
    mock_get_metadata["external:power_stat"] = None

    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "external:power_stat",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "statistics_not_defined",
                        "affected_entities": {("external:power_stat", None)},
                        "translation_placeholders": None,
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )


@test
async def validation_grid_power_recorder_untracked(
    hass: HomeAssistant = Depends(hass_fx),
    mock_energy_manager: EnergyManager = Depends(mock_energy_manager_fx),
    mock_is_entity_recorded: dict[str, bool] = Depends(mock_is_entity_recorded_fx),
    mock_get_metadata: dict[str, object] = Depends(mock_get_metadata_fx),
) -> None:
    """Test validating grid with power sensor not tracked by recorder."""
    mock_is_entity_recorded["sensor.untracked_power"] = False

    await mock_energy_manager.async_update(
        {
            "energy_sources": [
                {
                    "type": "grid",
                    "stat_rate": "sensor.untracked_power",
                    "cost_adjustment_day": 0.0,
                }
            ]
        }
    )

    result = await validate.async_validate(hass)
    expect(result.as_dict()).to_equal(
        {
            "energy_sources": [
                [
                    {
                        "type": "recorder_untracked",
                        "affected_entities": {("sensor.untracked_power", None)},
                        "translation_placeholders": None,
                    }
                ]
            ],
            "device_consumption": [],
            "device_consumption_water": [],
        }
    )
