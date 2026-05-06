"""Test the Utility Meter config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.utility_meter.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry, get_schema_suggested_value
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test.cases(test.case("sensor", platform="sensor"))
async def config_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    platform: str,
) -> None:
    """Test the config flow."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    with patch(
        "homeassistant.components.utility_meter.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "cycle": "monthly",
                "name": "Electricity meter",
                "offset": 0,
                "source": input_sensor_entity_id,
                "tariffs": [],
            },
        )
        await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Electricity meter")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "always_available": False,
            "source": input_sensor_entity_id,
            "tariffs": [],
        }
    )
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "always_available": False,
            "source": input_sensor_entity_id,
            "tariffs": [],
        }
    )
    expect(config_entry.title).to_equal("Electricity meter")


@test
async def tariffs(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test tariffs."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "cycle": "monthly",
            "name": "Electricity meter",
            "offset": 0,
            "source": input_sensor_entity_id,
            "tariffs": ["cat", "dog", "horse", "cow"],
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Electricity meter")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "periodically_resetting": True,
            "always_available": False,
            "offset": 0,
            "source": input_sensor_entity_id,
            "tariffs": ["cat", "dog", "horse", "cow"],
        }
    )

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "always_available": False,
            "source": input_sensor_entity_id,
            "tariffs": ["cat", "dog", "horse", "cow"],
        }
    )
    expect(config_entry.title).to_equal("Electricity meter")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "cycle": "monthly",
            "name": "Electricity meter",
            "offset": 0,
            "source": input_sensor_entity_id,
            "tariffs": ["cat", "cat", "cat", "cat"],
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]["base"]).to_equal("tariffs_not_unique")


@test
async def non_periodically_resetting(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test periodically resetting."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "cycle": "monthly",
            "name": "Electricity meter",
            "offset": 0,
            "periodically_resetting": False,
            "source": input_sensor_entity_id,
            "tariffs": [],
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Electricity meter")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "periodically_resetting": False,
            "always_available": False,
            "offset": 0,
            "source": input_sensor_entity_id,
            "tariffs": [],
        }
    )

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": False,
            "always_available": False,
            "source": input_sensor_entity_id,
            "tariffs": [],
        }
    )


@test
async def always_available(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test sensor always available."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "cycle": "monthly",
            "name": "Electricity meter",
            "offset": 0,
            "periodically_resetting": False,
            "source": input_sensor_entity_id,
            "tariffs": [],
            "always_available": True,
        },
    )
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Electricity meter")
    expect(result["data"]).to_equal({})
    expect(result["options"]).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "periodically_resetting": False,
            "always_available": True,
            "offset": 0,
            "source": input_sensor_entity_id,
            "tariffs": [],
        }
    )

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": False,
            "always_available": True,
            "source": input_sensor_entity_id,
            "tariffs": [],
        }
    )


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfiguring."""
    input_sensor1_entity_id = "sensor.input1"
    input_sensor2_entity_id = "sensor.input2"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": input_sensor1_entity_id,
            "tariffs": "",
        },
        title="Electricity meter",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")
    schema = result["data_schema"].schema
    expect(get_schema_suggested_value(schema, "source")).to_equal(
        input_sensor1_entity_id
    )
    expect(get_schema_suggested_value(schema, "periodically_resetting")).to_be(True)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "source": input_sensor2_entity_id,
            "periodically_resetting": False,
            "always_available": True,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": False,
            "always_available": True,
            "source": input_sensor2_entity_id,
            "tariffs": "",
        }
    )
    expect(config_entry.data).to_equal({})
    expect(config_entry.options).to_equal(
        {
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": False,
            "always_available": True,
            "source": input_sensor2_entity_id,
            "tariffs": "",
        }
    )
    expect(config_entry.title).to_equal("Electricity meter")

    await hass.async_block_till_done()


@test
async def change_device_source(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test remove the device registry configuration entry when the source entity changes."""
    source_config_entry_1 = MockConfigEntry()
    source_config_entry_1.add_to_hass(hass)
    source_device_entry_1 = device_registry.async_get_or_create(
        config_entry_id=source_config_entry_1.entry_id,
        identifiers={("sensor", "identifier_test1")},
        connections={("mac", "20:31:32:33:34:35")},
    )
    source_entity_1 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source1",
        config_entry=source_config_entry_1,
        device_id=source_device_entry_1.id,
    )

    source_config_entry_2 = MockConfigEntry()
    source_config_entry_2.add_to_hass(hass)
    source_device_entry_2 = device_registry.async_get_or_create(
        config_entry_id=source_config_entry_2.entry_id,
        identifiers={("sensor", "identifier_test2")},
        connections={("mac", "30:31:32:33:34:35")},
    )
    source_entity_2 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source2",
        config_entry=source_config_entry_2,
        device_id=source_device_entry_2.id,
    )

    source_config_entry_3 = MockConfigEntry()
    source_config_entry_3.add_to_hass(hass)
    source_entity_3 = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source3",
        config_entry=source_config_entry_3,
    )

    await hass.async_block_till_done()

    input_sensor_entity_id_1 = "sensor.test_source1"
    input_sensor_entity_id_2 = "sensor.test_source2"
    input_sensor_entity_id_3 = "sensor.test_source3"

    expect(entity_registry.async_get(input_sensor_entity_id_1) is not None).to_be(True)
    expect(entity_registry.async_get(input_sensor_entity_id_2) is not None).to_be(True)
    expect(entity_registry.async_get(input_sensor_entity_id_3) is not None).to_be(True)

    current_entity_source = source_entity_1
    utility_meter_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Energy",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
            "tariffs": [],
        },
        title="Energy",
    )
    utility_meter_config_entry.add_to_hass(hass)
    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    current_device = device_registry.async_get(
        device_id=current_entity_source.device_id
    )
    expect(
        utility_meter_config_entry.entry_id not in current_device.config_entries
    ).to_be(True)

    for utility_meter_entity in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(source_entity_1.device_id)

    previous_entity_source = source_entity_1
    current_entity_source = source_entity_2

    result = await hass.config_entries.options.async_init(
        utility_meter_config_entry.entry_id
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    await hass.async_block_till_done()

    previous_device = device_registry.async_get(
        device_id=previous_entity_source.device_id
    )
    expect(
        utility_meter_config_entry.entry_id not in previous_device.config_entries
    ).to_be(True)

    current_device = device_registry.async_get(
        device_id=current_entity_source.device_id
    )
    expect(
        utility_meter_config_entry.entry_id not in current_device.config_entries
    ).to_be(True)

    for utility_meter_entity in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(source_entity_2.device_id)

    previous_entity_source = source_entity_2
    current_entity_source = source_entity_3

    result = await hass.config_entries.options.async_init(
        utility_meter_config_entry.entry_id
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    await hass.async_block_till_done()

    previous_device = device_registry.async_get(
        device_id=previous_entity_source.device_id
    )
    expect(
        utility_meter_config_entry.entry_id not in previous_device.config_entries
    ).to_be(True)

    for utility_meter_entity in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_be(None)

    expect(
        dr.async_entries_for_config_entry(
            device_registry, utility_meter_config_entry.entry_id
        )
    ).to_equal([])

    previous_entity_source = source_entity_3
    current_entity_source = source_entity_2

    result = await hass.config_entries.options.async_init(
        utility_meter_config_entry.entry_id
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "periodically_resetting": True,
            "source": current_entity_source.entity_id,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    await hass.async_block_till_done()

    current_device = device_registry.async_get(
        device_id=current_entity_source.device_id
    )
    expect(
        utility_meter_config_entry.entry_id not in current_device.config_entries
    ).to_be(True)

    for utility_meter_entity in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(source_entity_2.device_id)
