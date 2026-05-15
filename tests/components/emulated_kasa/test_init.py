"""Tests for emulated_kasa library bindings."""

import math
from unittest.mock import AsyncMock, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import emulated_kasa
from homeassistant.components.emulated_kasa.const import (
    CONF_POWER,
    CONF_POWER_ENTITY,
    DOMAIN,
)
from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
)
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITIES,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture

ENTITY_SWITCH = "switch.ac"
ENTITY_SWITCH_NAME = "A/C"
ENTITY_SWITCH_POWER = 400.0
ENTITY_LIGHT = "light.bed_light"
ENTITY_LIGHT_NAME = "Bed Room Lights"
ENTITY_FAN = "fan.ceiling_fan"
ENTITY_FAN_NAME = "Ceiling Fan"
ENTITY_FAN_SPEED_LOW = 5
ENTITY_FAN_SPEED_MED = 10
ENTITY_FAN_SPEED_HIGH = 50
ENTITY_SENSOR = "sensor.outside_temperature"
ENTITY_SENSOR_NAME = "Power Sensor"

CONFIG = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SWITCH: {
                CONF_NAME: ENTITY_SWITCH_NAME,
                CONF_POWER: ENTITY_SWITCH_POWER,
            },
            ENTITY_LIGHT: {
                CONF_NAME: ENTITY_LIGHT_NAME,
                CONF_POWER_ENTITY: ENTITY_SENSOR,
            },
            ENTITY_FAN: {
                CONF_POWER: "{% if is_state_attr('"
                + ENTITY_FAN
                + "','percentage', 33) %} "
                + str(ENTITY_FAN_SPEED_LOW)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','percentage', 66) %} "
                + str(ENTITY_FAN_SPEED_MED)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','percentage', 100) %} "
                + str(ENTITY_FAN_SPEED_HIGH)
                + "{% endif %}"
            },
        }
    }
}

CONFIG_SWITCH = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SWITCH: {
                CONF_NAME: ENTITY_SWITCH_NAME,
                CONF_POWER: ENTITY_SWITCH_POWER,
            },
        }
    }
}

CONFIG_SWITCH_NO_POWER = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SWITCH: {},
        }
    }
}

CONFIG_LIGHT = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_LIGHT: {
                CONF_NAME: ENTITY_LIGHT_NAME,
                CONF_POWER_ENTITY: ENTITY_SENSOR,
            },
        }
    }
}

CONFIG_FAN = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_FAN: {
                CONF_POWER: "{% if is_state_attr('"
                + ENTITY_FAN
                + "','percentage', 33) %} "
                + str(ENTITY_FAN_SPEED_LOW)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','percentage', 66) %} "
                + str(ENTITY_FAN_SPEED_MED)
                + "{% elif is_state_attr('"
                + ENTITY_FAN
                + "','percentage', 100) %} "
                + str(ENTITY_FAN_SPEED_HIGH)
                + "{% endif %}"
            },
        }
    }
}


CONFIG_SENSOR = {
    DOMAIN: {
        CONF_ENTITIES: {
            ENTITY_SENSOR: {CONF_NAME: ENTITY_SENSOR_NAME},
        }
    }
}


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Set up the homeassistant integration and act as the module anchor."""
    await async_setup_component(hass, "homeassistant", {})
    return hass


def nested_value(ndict, *keys):
    """Return a nested dict value  or None if it doesn't exist."""
    if len(keys) == 0:
        return ndict
    key = keys[0]
    if not isinstance(ndict, dict) or key not in ndict:
        return None
    return nested_value(ndict[key], *keys[1:])


@test
async def setup(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that devices are reported correctly."""
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(await async_setup_component(hass, DOMAIN, CONFIG) is True).to_be(True)


@test
async def float_(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a configuration using a simple float."""
    config = CONFIG_SWITCH[DOMAIN][CONF_ENTITIES]
    expect(
        await async_setup_component(
            hass,
            SWITCH_DOMAIN,
            {SWITCH_DOMAIN: {"platform": "demo"}},
        )
    ).to_be(True)
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(
            await async_setup_component(hass, DOMAIN, CONFIG_SWITCH) is True
        ).to_be(True)
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn switch on
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()

    switch = hass.states.get(ENTITY_SWITCH)
    expect(switch.state).to_equal(STATE_ON)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()

    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_SWITCH_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, ENTITY_SWITCH_POWER)).to_be(True)

    # Turn off
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await hass.async_block_till_done()

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_SWITCH_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 0)).to_be(True)


@test
async def switch_power(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a configuration using a simple float."""
    config = CONFIG_SWITCH_NO_POWER[DOMAIN][CONF_ENTITIES]
    expect(
        await async_setup_component(
            hass,
            SWITCH_DOMAIN,
            {SWITCH_DOMAIN: {"platform": "demo"}},
        )
    ).to_be(True)
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(
            await async_setup_component(hass, DOMAIN, CONFIG_SWITCH_NO_POWER) is True
        ).to_be(True)
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn switch on
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )

    # Turn off
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal("AC")
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 0)).to_be(True)


@test
async def template(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a configuration using a complex template."""
    config = CONFIG_FAN[DOMAIN][CONF_ENTITIES]
    expect(
        await async_setup_component(
            hass, FAN_DOMAIN, {FAN_DOMAIN: {"platform": "demo"}}
        )
    ).to_be(True)
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(
            await async_setup_component(hass, DOMAIN, CONFIG_FAN) is True
        ).to_be(True)
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn all devices on to known state
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_PERCENTAGE: 33},
        blocking=True,
    )
    await hass.async_block_till_done()

    fan = hass.states.get(ENTITY_FAN)
    expect(fan.state).to_equal(STATE_ON)

    # Fan low:
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_FAN_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, ENTITY_FAN_SPEED_LOW)).to_be(True)

    # Fan High:
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_PERCENTAGE: 100},
        blocking=True,
    )
    await hass.async_block_till_done()
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_FAN_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, ENTITY_FAN_SPEED_HIGH)).to_be(True)

    # Fan off:
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await hass.async_block_till_done()
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_FAN_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 0)).to_be(True)


@test
async def sensor(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a configuration using a sensor in a template."""
    config = CONFIG_LIGHT[DOMAIN][CONF_ENTITIES]
    expect(
        await async_setup_component(
            hass, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
        )
    ).to_be(True)
    expect(
        await async_setup_component(
            hass,
            SENSOR_DOMAIN,
            {SENSOR_DOMAIN: {"platform": "demo"}},
        )
    ).to_be(True)
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(
            await async_setup_component(hass, DOMAIN, CONFIG_LIGHT) is True
        ).to_be(True)
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )
    hass.states.async_set(ENTITY_SENSOR, 35)

    light = hass.states.get(ENTITY_LIGHT)
    expect(light.state).to_equal(STATE_ON)
    sensor_state = hass.states.get(ENTITY_SENSOR)
    expect(sensor_state.state).to_equal("35")

    # light
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_LIGHT_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 35)).to_be(True)

    # change power sensor
    hass.states.async_set(ENTITY_SENSOR, 40)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_LIGHT_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 40)).to_be(True)

    # report 0 if device is off
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_LIGHT_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 0)).to_be(True)


@test
async def sensor_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test a configuration using a sensor in a template."""
    config = CONFIG_SENSOR[DOMAIN][CONF_ENTITIES]
    expect(
        await async_setup_component(
            hass,
            SENSOR_DOMAIN,
            {SENSOR_DOMAIN: {"platform": "demo"}},
        )
    ).to_be(True)
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(
            await async_setup_component(hass, DOMAIN, CONFIG_SENSOR) is True
        ).to_be(True)
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    hass.states.async_set(ENTITY_SENSOR, 35)

    sensor_state = hass.states.get(ENTITY_SENSOR)
    expect(sensor_state.state).to_equal("35")

    # sensor
    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_SENSOR_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 35)).to_be(True)

    # change power sensor
    hass.states.async_set(ENTITY_SENSOR, 40)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_SENSOR_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 40)).to_be(True)

    # report 0 if device is off
    hass.states.async_set(ENTITY_SENSOR, 0)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_SENSOR_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 0)).to_be(True)


@test
async def multiple_devices(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test that devices are reported correctly."""
    config = CONFIG[DOMAIN][CONF_ENTITIES]
    expect(
        await async_setup_component(
            hass, SWITCH_DOMAIN, {SWITCH_DOMAIN: {"platform": "demo"}}
        )
    ).to_be(True)
    expect(
        await async_setup_component(
            hass, LIGHT_DOMAIN, {LIGHT_DOMAIN: {"platform": "demo"}}
        )
    ).to_be(True)
    expect(
        await async_setup_component(
            hass, FAN_DOMAIN, {FAN_DOMAIN: {"platform": "demo"}}
        )
    ).to_be(True)
    expect(
        await async_setup_component(
            hass,
            SENSOR_DOMAIN,
            {SENSOR_DOMAIN: {"platform": "demo"}},
        )
    ).to_be(True)
    with patch(
        "sense_energy.SenseLink",
        return_value=Mock(start=AsyncMock(), close=AsyncMock()),
    ):
        expect(await emulated_kasa.async_setup(hass, CONFIG) is True).to_be(True)
    await hass.async_block_till_done()
    await emulated_kasa.validate_configs(hass, config)

    # Turn all devices on to known state
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_SWITCH}, blocking=True
    )
    await hass.services.async_call(
        LIGHT_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_LIGHT}, blocking=True
    )
    hass.states.async_set(ENTITY_SENSOR, 35)
    await hass.services.async_call(
        FAN_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_FAN}, blocking=True
    )
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {ATTR_ENTITY_ID: ENTITY_FAN, ATTR_PERCENTAGE: 66},
        blocking=True,
    )
    await hass.async_block_till_done()

    # All of them should now be on
    switch = hass.states.get(ENTITY_SWITCH)
    expect(switch.state).to_equal(STATE_ON)
    light = hass.states.get(ENTITY_LIGHT)
    expect(light.state).to_equal(STATE_ON)
    sensor_state = hass.states.get(ENTITY_SENSOR)
    expect(sensor_state.state).to_equal("35")
    fan = hass.states.get(ENTITY_FAN)
    expect(fan.state).to_equal(STATE_ON)

    plug_it = emulated_kasa.get_plug_devices(hass, config)
    # switch
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_SWITCH_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, ENTITY_SWITCH_POWER)).to_be(True)

    # light
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_LIGHT_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, 35)).to_be(True)

    # fan
    plug = next(plug_it).generate_response()
    expect(nested_value(plug, "system", "get_sysinfo", "alias")).to_equal(
        ENTITY_FAN_NAME
    )
    power = nested_value(plug, "emeter", "get_realtime", "power")
    expect(math.isclose(power, ENTITY_FAN_SPEED_MED)).to_be(True)

    # No more devices
    expect(next(plug_it, None) is None).to_be(True)
