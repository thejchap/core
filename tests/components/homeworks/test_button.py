"""Tests for the Lutron Homeworks Series 4 and 8 button."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.homeworks.const import (
    CONF_ADDR,
    CONF_BUTTONS,
    CONF_CONTROLLER_ID,
    CONF_DIMMERS,
    CONF_KEYPADS,
    CONF_LED,
    CONF_NUMBER,
    CONF_RATE,
    CONF_RELEASE_DELAY,
    DOMAIN,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from ._fixtures import mock_homeworks

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


CONFIG_ENTRY_OPTIONS = {
    CONF_CONTROLLER_ID: "main_controller",
    CONF_HOST: "192.168.0.1",
    CONF_PORT: 1234,
    CONF_DIMMERS: [
        {
            CONF_ADDR: "[02:08:01:01]",
            CONF_NAME: "Foyer Sconces",
            CONF_RATE: 1.0,
        }
    ],
    CONF_KEYPADS: [
        {
            CONF_ADDR: "[02:08:02:01]",
            CONF_NAME: "Foyer Keypad",
            CONF_BUTTONS: [
                {
                    CONF_NAME: "Morning",
                    CONF_NUMBER: 1,
                    CONF_LED: True,
                    CONF_RELEASE_DELAY: None,
                },
                {
                    CONF_NAME: "Relax",
                    CONF_NUMBER: 2,
                    CONF_LED: True,
                    CONF_RELEASE_DELAY: None,
                },
                {
                    CONF_NAME: "Dim up",
                    CONF_NUMBER: 3,
                    CONF_LED: False,
                    CONF_RELEASE_DELAY: 0.2,
                },
            ],
        }
    ],
}


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Lutron Homeworks",
        domain=DOMAIN,
        data={CONF_PASSWORD: None, CONF_USERNAME: None},
        options=CONFIG_ENTRY_OPTIONS,
    )


@test
async def button_service_calls(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    homeworks: MagicMock = Depends(mock_homeworks),
) -> None:
    """Test Homeworks button service call."""
    entity_id = "button.foyer_keypad_morning"
    mock_controller = MagicMock()
    homeworks.return_value = mock_controller

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_id in hass.states.async_entity_ids(BUTTON_DOMAIN)).to_be(True)

    mock_controller._send.reset_mock()
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    expect(len(mock_controller._send.mock_calls)).to_equal(1)
    expect(mock_controller._send.mock_calls[0][1]).to_equal(
        ("KBP, [02:08:02:01], 1",)
    )


@test
async def button_service_calls_delay(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    homeworks: MagicMock = Depends(mock_homeworks),
) -> None:
    """Test Homeworks button service call with release delay."""
    entity_id = "button.foyer_keypad_dim_up"
    mock_controller = MagicMock()
    homeworks.return_value = mock_controller

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(entity_id in hass.states.async_entity_ids(BUTTON_DOMAIN)).to_be(True)

    mock_controller._send.reset_mock()
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )
    expect(len(mock_controller._send.mock_calls)).to_equal(2)
    expect(mock_controller._send.mock_calls[0][1]).to_equal(
        ("KBP, [02:08:02:01], 3",)
    )
    expect(mock_controller._send.mock_calls[1][1]).to_equal(
        ("KBR, [02:08:02:01], 3",)
    )
