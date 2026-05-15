"""Test the Kegtron sensors."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.kegtron.const import DOMAIN
from homeassistant.components.sensor import ATTR_STATE_CLASS
from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant

from . import (
    KEGTRON_KT100_SERVICE_INFO,
    KEGTRON_KT200_PORT_1_SERVICE_INFO,
    KEGTRON_KT200_PORT_2_SERVICE_INFO,
)

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def sensors_kt100(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors for Kegtron KT-100."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="D0:CF:5E:5C:9B:75",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(0)

    inject_bluetooth_service_info(
        hass,
        KEGTRON_KT100_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all("sensor"))).to_equal(7)

    port_count_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_port_count")
    port_count_sensor_attrs = port_count_sensor.attributes
    expect(port_count_sensor.state).to_equal("Single port device")
    expect(port_count_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Port Count"
    )

    keg_size_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_keg_size")
    keg_size_sensor_attrs = keg_size_sensor.attributes
    expect(keg_size_sensor.state).to_equal("18.927")
    expect(keg_size_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Keg Size"
    )
    expect(keg_size_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")

    keg_type_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_keg_type")
    keg_type_sensor_attrs = keg_type_sensor.attributes
    expect(keg_type_sensor.state).to_equal("Corny (5.0 gal)")
    expect(keg_type_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Keg Type"
    )

    volume_start_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_volume_start")
    volume_start_sensor_attrs = volume_start_sensor.attributes
    expect(volume_start_sensor.state).to_equal("5.0")
    expect(volume_start_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Volume Start"
    )
    expect(volume_start_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")

    volume_dispensed_sensor = hass.states.get(
        "sensor.kegtron_kt_100_9b75_volume_dispensed"
    )
    volume_dispensed_attrs = volume_dispensed_sensor.attributes
    expect(volume_dispensed_sensor.state).to_equal("0.738")
    expect(volume_dispensed_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Volume Dispensed"
    )
    expect(volume_dispensed_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")
    expect(volume_dispensed_attrs[ATTR_STATE_CLASS]).to_equal("total")

    port_state_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_port_state")
    port_state_sensor_attrs = port_state_sensor.attributes
    expect(port_state_sensor.state).to_equal("Configured")
    expect(port_state_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Port State"
    )

    port_name_sensor = hass.states.get("sensor.kegtron_kt_100_9b75_port_name")
    port_name_attrs = port_name_sensor.attributes
    expect(port_name_sensor.state).to_equal("Single Port")
    expect(port_name_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-100 9B75 Port Name"
    )

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()


@test
async def sensors_kt200(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setting up creates the sensors for Kegtron KT-200."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="D0:CF:5E:5C:9B:75",
    )
    entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all("sensor"))).to_equal(0)

    # Kegtron KT-200 has two ports that are reported separately, start with port 2
    inject_bluetooth_service_info(
        hass,
        KEGTRON_KT200_PORT_2_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all("sensor"))).to_equal(7)

    port_count_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_port_count")
    port_count_sensor_attrs = port_count_sensor.attributes
    expect(port_count_sensor.state).to_equal("Dual port device")
    expect(port_count_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Port Count"
    )

    keg_size_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_keg_size_port_2")
    keg_size_sensor_attrs = keg_size_sensor.attributes
    expect(keg_size_sensor.state).to_equal("58.93")
    expect(keg_size_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Keg Size Port 2"
    )
    expect(keg_size_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")

    keg_type_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_keg_type_port_2")
    keg_type_sensor_attrs = keg_type_sensor.attributes
    expect(keg_type_sensor.state).to_equal("Other (58.93 L)")
    expect(keg_type_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Keg Type Port 2"
    )

    volume_start_sensor = hass.states.get(
        "sensor.kegtron_kt_200_9b75_volume_start_port_2"
    )
    volume_start_sensor_attrs = volume_start_sensor.attributes
    expect(volume_start_sensor.state).to_equal("15.0")
    expect(volume_start_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Volume Start Port 2"
    )
    expect(volume_start_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")

    volume_dispensed_sensor = hass.states.get(
        "sensor.kegtron_kt_200_9b75_volume_dispensed_port_2"
    )
    volume_dispensed_attrs = volume_dispensed_sensor.attributes
    expect(volume_dispensed_sensor.state).to_equal("0.738")
    expect(volume_dispensed_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Volume Dispensed Port 2"
    )
    expect(volume_dispensed_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")
    expect(volume_dispensed_attrs[ATTR_STATE_CLASS]).to_equal("total")

    port_state_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_port_state_port_2")
    port_state_sensor_attrs = port_state_sensor.attributes
    expect(port_state_sensor.state).to_equal("Configured")
    expect(port_state_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Port State Port 2"
    )

    port_name_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_port_name_port_2")
    port_name_attrs = port_name_sensor.attributes
    expect(port_name_sensor.state).to_equal("2nd Port")
    expect(port_name_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Port Name Port 2"
    )

    # Followed by a BLE advertisement of port 1
    inject_bluetooth_service_info(
        hass,
        KEGTRON_KT200_PORT_1_SERVICE_INFO,
    )
    await hass.async_block_till_done()
    expect(len(hass.states.async_all("sensor"))).to_equal(13)

    port_count_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_port_count")
    port_count_sensor_attrs = port_count_sensor.attributes
    expect(port_count_sensor.state).to_equal("Dual port device")
    expect(port_count_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Port Count"
    )

    keg_size_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_keg_size_port_1")
    keg_size_sensor_attrs = keg_size_sensor.attributes
    expect(keg_size_sensor.state).to_equal("9.04")
    expect(keg_size_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Keg Size Port 1"
    )
    expect(keg_size_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")

    keg_type_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_keg_type_port_1")
    keg_type_sensor_attrs = keg_type_sensor.attributes
    expect(keg_type_sensor.state).to_equal("Other (9.04 L)")
    expect(keg_type_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Keg Type Port 1"
    )

    volume_start_sensor = hass.states.get(
        "sensor.kegtron_kt_200_9b75_volume_start_port_1"
    )
    volume_start_sensor_attrs = volume_start_sensor.attributes
    expect(volume_start_sensor.state).to_equal("50.0")
    expect(volume_start_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Volume Start Port 1"
    )
    expect(volume_start_sensor_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")

    volume_dispensed_sensor = hass.states.get(
        "sensor.kegtron_kt_200_9b75_volume_dispensed_port_1"
    )
    volume_dispensed_attrs = volume_dispensed_sensor.attributes
    expect(volume_dispensed_sensor.state).to_equal("13.0")
    expect(volume_dispensed_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Volume Dispensed Port 1"
    )
    expect(volume_dispensed_attrs[ATTR_UNIT_OF_MEASUREMENT]).to_equal("L")
    expect(volume_dispensed_attrs[ATTR_STATE_CLASS]).to_equal("total")

    port_state_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_port_state_port_1")
    port_state_sensor_attrs = port_state_sensor.attributes
    expect(port_state_sensor.state).to_equal("Configured")
    expect(port_state_sensor_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Port State Port 1"
    )

    port_name_sensor = hass.states.get("sensor.kegtron_kt_200_9b75_port_name_port_1")
    port_name_attrs = port_name_sensor.attributes
    expect(port_name_sensor.state).to_equal("Port 1")
    expect(port_name_attrs[ATTR_FRIENDLY_NAME]).to_equal(
        "Kegtron KT-200 9B75 Port Name Port 1"
    )

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
