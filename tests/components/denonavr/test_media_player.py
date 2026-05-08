"""The tests for the denonavr media player platform."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import media_player
from homeassistant.components.denonavr.config_flow import (
    CONF_MANUFACTURER,
    CONF_SERIAL_NUMBER,
    CONF_TYPE,
    DOMAIN,
)
from homeassistant.components.denonavr.const import ATTR_DYNAMIC_EQ
from homeassistant.components.denonavr.services import (
    ATTR_COMMAND,
    SERVICE_GET_COMMAND,
    SERVICE_SET_DYNAMIC_EQ,
    SERVICE_UPDATE_AUDYSSEY,
)
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_MODEL
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


TEST_HOST = "1.2.3.4"
TEST_NAME = "Test_Receiver"
TEST_MODEL = "model5"
TEST_SERIALNUMBER = "123456789"
TEST_MANUFACTURER = "Denon"
TEST_RECEIVER_TYPE = "avr-x"
TEST_ZONE = "Main"
TEST_UNIQUE_ID = f"{TEST_MODEL}-{TEST_SERIALNUMBER}"
ENTITY_ID = f"{media_player.DOMAIN}.{TEST_NAME}"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@fixture
def client() -> Generator[MagicMock]:
    """Patch of client library for tests."""
    with (
        patch(
            "homeassistant.components.denonavr.receiver.DenonAVR",
            autospec=True,
        ) as mock_client_class,
        patch("homeassistant.components.denonavr.config_flow.denonavr.async_discover"),
    ):
        mock_client_class.return_value.name = TEST_NAME
        mock_client_class.return_value.model_name = TEST_MODEL
        mock_client_class.return_value.serial_number = TEST_SERIALNUMBER
        mock_client_class.return_value.manufacturer = TEST_MANUFACTURER
        mock_client_class.return_value.receiver_type = TEST_RECEIVER_TYPE
        mock_client_class.return_value.zone = TEST_ZONE
        mock_client_class.return_value.input_func_list = []
        mock_client_class.return_value.sound_mode_list = []
        mock_client_class.return_value.zones = {"Main": mock_client_class.return_value}
        yield mock_client_class.return_value


async def _setup_denonavr(hass: HomeAssistant) -> None:
    """Initialize media_player for tests."""
    entry_data = {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
    }

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_UNIQUE_ID,
        data=entry_data,
    )
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    expect(state).not_.to_be(None)
    expect(state.name).to_equal(TEST_NAME)


@test
async def get_command(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
) -> None:
    """Test generic command functionality."""
    await _setup_denonavr(hass)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_COMMAND: "test_command",
    }
    await hass.services.async_call(DOMAIN, SERVICE_GET_COMMAND, data)
    await hass.async_block_till_done()

    client.async_get_command.assert_awaited_with("test_command")


@test
async def dynamic_eq(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
) -> None:
    """Test that dynamic eq method works."""
    await _setup_denonavr(hass)

    data = {
        ATTR_ENTITY_ID: ENTITY_ID,
        ATTR_DYNAMIC_EQ: True,
    }
    await hass.services.async_call(DOMAIN, SERVICE_SET_DYNAMIC_EQ, data)
    await hass.async_block_till_done()

    data[ATTR_DYNAMIC_EQ] = False
    await hass.services.async_call(DOMAIN, SERVICE_SET_DYNAMIC_EQ, data)
    await hass.async_block_till_done()

    client.async_dynamic_eq_on.assert_called_once()
    client.async_dynamic_eq_off.assert_called_once()


@test
async def update_audyssey(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: MagicMock = Depends(client),
) -> None:
    """Test that dynamic eq method works."""
    await _setup_denonavr(hass)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_UPDATE_AUDYSSEY,
        {ATTR_ENTITY_ID: ENTITY_ID},
    )
    await hass.async_block_till_done()

    client.async_update_audyssey.assert_called_once()
