"""Tryke skip stub (pending port)."""

from datetime import timedelta
from unittest.mock import Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def temperature_readback(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test for reading sensors."""
    mock_temper_device = Mock()
    mock_temper_device.get_temperature.return_value = 12.3

    utcnow = dt_util.utcnow()

    with patch(
        "temperusb.temper.TemperHandler.get_devices",
        return_value=[mock_temper_device],
    ):
        await async_setup_component(
            hass,
            "sensor",
            {"sensor": {"platform": "temper", "name": "mydevicename"}},
        )
        await hass.async_block_till_done()

        async_fire_time_changed(hass, utcnow + timedelta(seconds=70))
        await hass.async_block_till_done(wait_background_tasks=True)

        temperature = hass.states.get("sensor.mydevicename")
        expect(temperature is not None).to_be(True)
        expect(temperature.state).to_equal("12.3")
