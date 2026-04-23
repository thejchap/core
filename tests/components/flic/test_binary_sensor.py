"""Tests for Flic button integration."""

from unittest import mock

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import entity_registry, hass


class _MockFlicClient:
    def __init__(self, button_addresses) -> None:
        self.addresses = button_addresses
        self.get_info_callback = None
        self.scan_wizard = None
        self.channel = None

    def close(self):
        pass

    def get_info(self, callback):
        self.get_info_callback = callback
        callback({"bd_addr_of_verified_buttons": self.addresses})

    def handle_events(self):
        pass

    def add_scan_wizard(self, wizard):
        self.scan_wizard = wizard

    def add_connection_channel(self, channel):
        self.channel = channel


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def button_uid(
    hass: HomeAssistant = Depends(hass),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test UID assignment for Flic buttons."""
    address_to_name = {
        "80:e4:da:78:6e:11": "binary_sensor.flic_80e4da786e11",
        "80:E4:DA:78:6E:12": "binary_sensor.flic_80e4da786e12",
    }

    flic_client = _MockFlicClient(tuple(address_to_name))

    with mock.patch.multiple(
        "pyflic",
        FlicClient=lambda _, __: flic_client,
        ButtonConnectionChannel=mock.DEFAULT,
        ScanWizard=mock.DEFAULT,
    ):
        result = await async_setup_component(
            hass,
            "binary_sensor",
            {"binary_sensor": [{"platform": "flic"}]},
        )
        expect(result).to_be(True)

        await hass.async_block_till_done()

        for address, name in address_to_name.items():
            state = hass.states.get(name)
            expect(state is not None).to_be(True)
            expect(state.attributes.get("address")).to_equal(address)

            entry = entity_registry.async_get(name)
            expect(entry is not None).to_be(True)
            expect(entry.unique_id).to_equal(address.lower())
