"""Test the Random config flow."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test
from voluptuous import Invalid

from homeassistant import config_entries
from homeassistant.components.random import async_setup_entry
from homeassistant.components.random.const import DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("binary_sensor_empty", "binary_sensor", {}, {}),
    test.case(
        "sensor_with_power",
        "sensor",
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
        },
        {
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            "minimum": 0,
            "maximum": 20,
        },
    ),
    test.case("sensor_default_range", "sensor", {}, {"minimum": 0, "maximum": 20}),
)
async def config_flow(
    entity_type: str,
    extra_input: dict[str, Any],
    extra_options: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": entity_type},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(entity_type)

    with patch(
        "homeassistant.components.random.async_setup_entry", wraps=async_setup_entry
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My random entity",
                **extra_input,
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("My random entity")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "name": "My random entity",
            "entity_type": entity_type,
            **extra_options,
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("power_wh", SensorDeviceClass.POWER, UnitOfEnergy.WATT_HOUR),
    test.case("illuminance_wh", SensorDeviceClass.ILLUMINANCE, UnitOfEnergy.WATT_HOUR),
)
async def wrong_uom(
    device_class: SensorDeviceClass,
    unit_of_measurement: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test entering a wrong unit of measurement."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.MENU)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "sensor"},
    )
    await hass.async_block_till_done()
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("sensor")

    async def _try_configure() -> None:
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My random entity",
                "device_class": device_class,
                "unit_of_measurement": unit_of_measurement,
            },
        )

    raised: Exception | None = None
    try:
        await _try_configure()
    except Invalid as err:
        raised = err
    expect(raised is not None).to_be(True)
    expect("is not a valid unit for device class" in str(raised)).to_be(True)


@test.cases(
    test.case(
        "sensor_energy_to_power",
        "sensor",
        {
            "device_class": SensorDeviceClass.ENERGY,
            "unit_of_measurement": UnitOfEnergy.WATT_HOUR,
            "minimum": 0,
            "maximum": 20,
        },
        {
            "minimum": 10,
            "maximum": 20,
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
        },
    ),
)
async def options(
    entity_type: str,
    extra_options: dict[str, Any],
    options_options: dict[str, Any],
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test reconfiguring."""

    random_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My random",
            "entity_type": entity_type,
            **extra_options,
        },
        title="My random",
    )
    random_config_entry.add_to_hass(hass)

    setup_ok = await hass.config_entries.async_setup(random_config_entry.entry_id)
    expect(setup_ok).to_be(True)
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal(entity_type)
    expect("name" not in result["data_schema"].schema).to_be(True)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=options_options,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "name": "My random",
            "entity_type": entity_type,
            **options_options,
        }
    )
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "name": "My random",
            "entity_type": entity_type,
            **options_options,
        }
    )
    expect(config_entry.title).to_equal("My random")
