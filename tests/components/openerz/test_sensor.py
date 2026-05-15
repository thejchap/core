"""Tryke skip stub (pending port)."""

from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_CONFIG = {
    "sensor": {
        "platform": "openerz",
        "name": "test_name",
        "zip": 1234,
        "waste_type": "glass",
    }
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture so tryke fully resolves Depends across the module."""


@test
async def sensor_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test whether default waste type set properly."""
    with patch(
        "homeassistant.components.openerz.sensor.OpenERZConnector"
    ) as patched_connector:
        pickup_instance = MagicMock()
        pickup_instance.find_next_pickup.return_value = "2020-12-12"
        patched_connector.return_value = pickup_instance

        await async_setup_component(hass, SENSOR_DOMAIN, MOCK_CONFIG)
        await hass.async_block_till_done()

        entity_id = "sensor.test_name"
        test_openerz_state = hass.states.get(entity_id)

        expect(test_openerz_state.state).to_equal("2020-12-12")
        expect(test_openerz_state.name).to_equal("test_name")
        pickup_instance.find_next_pickup.assert_called_once()
