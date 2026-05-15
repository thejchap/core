"""Pytest modules for Aurora ABB Powerone PV inverter sensor integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.aurora_abb_powerone.const import (
    ATTR_FIRMWARE,
    ATTR_MODEL,
    DOMAIN,
)
from homeassistant.const import ATTR_SERIAL_NUMBER, CONF_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def unload_entry(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test unloading the aurora_abb_powerone entry."""

    with (
        patch("aurorapy.client.AuroraSerialClient.connect", return_value=None),
        patch(
            "aurorapy.client.AuroraSerialClient.serial_number",
            return_value="9876543",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.version",
            return_value="9.8.7.6",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.pn",
            return_value="A.B.C",
        ),
        patch(
            "aurorapy.client.AuroraSerialClient.firmware",
            return_value="1.234",
        ),
    ):
        mock_entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                CONF_PORT: "/dev/ttyUSB7",
                CONF_ADDRESS: 7,
                ATTR_MODEL: "model123",
                ATTR_SERIAL_NUMBER: "876",
                ATTR_FIRMWARE: "1.2.3.4",
            },
        )
        mock_entry.add_to_hass(hass)
        expect(await async_setup_component(hass, DOMAIN, {})).to_be_truthy()
        await hass.async_block_till_done()
        expect(
            await hass.config_entries.async_unload(mock_entry.entry_id)
        ).to_be_truthy()
        await hass.async_block_till_done()
