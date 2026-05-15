"""Test the Energy helpers."""

from tryke import expect, test

from homeassistant.components.energy.helpers import (
    generate_power_sensor_entity_id,
    generate_power_sensor_unique_id,
)


@test
def generate_power_sensor_unique_id_inverted() -> None:
    """Test unique ID generation for inverted power config."""
    config = {"stat_rate_inverted": "sensor.battery_power"}
    unique_id = generate_power_sensor_unique_id("battery", config)
    expect(unique_id).to_equal("energy_power_battery_inverted_sensor_battery_power")


@test
def generate_power_sensor_unique_id_combined() -> None:
    """Test unique ID generation for combined power config."""
    config = {
        "stat_rate_from": "sensor.battery_discharge",
        "stat_rate_to": "sensor.battery_charge",
    }
    unique_id = generate_power_sensor_unique_id("battery", config)
    expect(unique_id).to_equal(
        "energy_power_battery_combined_sensor_battery_discharge_sensor_battery_charge"
    )


@test
def generate_power_sensor_unique_id_standard() -> None:
    """Test unique ID generation raises for standard config (schema-invalid)."""
    config = {"stat_rate": "sensor.battery_power"}
    expect(lambda: generate_power_sensor_unique_id("battery", config)).to_raise(
        RuntimeError, match="Invalid power config"
    )


@test
def generate_power_sensor_unique_id_empty() -> None:
    """Test unique ID generation raises for empty config (schema-invalid)."""
    config: dict[str, str] = {}
    expect(lambda: generate_power_sensor_unique_id("battery", config)).to_raise(
        RuntimeError, match="Invalid power config"
    )


@test
def generate_power_sensor_unique_id_grid() -> None:
    """Test unique ID generation for grid source type."""
    config = {"stat_rate_inverted": "sensor.grid_power"}
    unique_id = generate_power_sensor_unique_id("grid", config)
    expect(unique_id).to_equal("energy_power_grid_inverted_sensor_grid_power")


@test
def generate_power_sensor_entity_id_inverted_with_prefix() -> None:
    """Test entity ID generation for inverted config with sensor prefix."""
    config = {"stat_rate_inverted": "sensor.battery_power"}
    entity_id = generate_power_sensor_entity_id("battery", config)
    expect(entity_id).to_equal("sensor.battery_power_inverted")


@test
def generate_power_sensor_entity_id_inverted_without_prefix() -> None:
    """Test entity ID generation for inverted config without sensor prefix."""
    config = {"stat_rate_inverted": "custom.battery_power"}
    entity_id = generate_power_sensor_entity_id("battery", config)
    expect(entity_id).to_equal("sensor.custom_battery_power_inverted")


@test
def generate_power_sensor_entity_id_combined() -> None:
    """Test entity ID generation for combined power config."""
    config = {
        "stat_rate_from": "sensor.battery_discharge",
        "stat_rate_to": "sensor.battery_charge",
    }
    entity_id = generate_power_sensor_entity_id("battery", config)
    expect(entity_id).to_equal(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )


@test
def generate_power_sensor_entity_id_combined_without_prefix() -> None:
    """Test entity ID generation for combined config without sensor prefix."""
    config = {
        "stat_rate_from": "battery_discharge",
        "stat_rate_to": "battery_charge",
    }
    entity_id = generate_power_sensor_entity_id("battery", config)
    expect(entity_id).to_equal(
        "sensor.energy_battery_battery_discharge_battery_charge_net_power"
    )


@test
def generate_power_sensor_entity_id_standard() -> None:
    """Test entity ID generation raises for standard config (schema-invalid)."""
    config = {"stat_rate": "sensor.battery_power"}
    expect(lambda: generate_power_sensor_entity_id("battery", config)).to_raise(
        RuntimeError, match="Invalid power config"
    )


@test
def generate_power_sensor_entity_id_empty() -> None:
    """Test entity ID generation raises for empty config (schema-invalid)."""
    config: dict[str, str] = {}
    expect(lambda: generate_power_sensor_entity_id("battery", config)).to_raise(
        RuntimeError, match="Invalid power config"
    )


@test
def generate_power_sensor_entity_id_grid() -> None:
    """Test entity ID generation for grid source type."""
    config = {
        "stat_rate_from": "sensor.grid_import",
        "stat_rate_to": "sensor.grid_export",
    }
    entity_id = generate_power_sensor_entity_id("grid", config)
    expect(entity_id).to_equal(
        "sensor.energy_grid_grid_import_grid_export_net_power"
    )
