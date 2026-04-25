"""Test the Firmata config flow."""

from unittest.mock import patch

from pymata_express.pymata_express_serial import serial
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.firmata.const import CONF_SERIAL_PORT, DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def import_cannot_connect_pymata(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we fail with an invalid board."""
    with patch(
        "homeassistant.components.firmata.board.PymataExpress.start_aio",
        side_effect=RuntimeError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def import_cannot_connect_serial(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we fail with an invalid board."""
    with patch(
        "homeassistant.components.firmata.board.PymataExpress.start_aio",
        side_effect=serial.SerialException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def import_cannot_connect_serial_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we fail with an invalid board."""
    with patch(
        "homeassistant.components.firmata.board.PymataExpress.start_aio",
        side_effect=serial.SerialTimeoutException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")


@test
async def import_(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we create an entry from config."""
    with (
        patch("homeassistant.components.firmata.board.PymataExpress", autospec=True),
        patch(
            "homeassistant.components.firmata.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.firmata.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_SERIAL_PORT: "/dev/nonExistent"},
        )

        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("serial-/dev/nonExistent")
        expect(result["data"]).to_equal(
            {
                CONF_NAME: "serial-/dev/nonExistent",
                CONF_SERIAL_PORT: "/dev/nonExistent",
            }
        )
        await hass.async_block_till_done()
        expect(len(mock_setup.mock_calls)).to_equal(1)
        expect(len(mock_setup_entry.mock_calls)).to_equal(1)
