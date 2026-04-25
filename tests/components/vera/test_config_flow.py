"""Vera tests."""

from unittest.mock import AsyncMock, MagicMock, patch

from requests.exceptions import RequestException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.vera.const import (
    CONF_CONTROLLER,
    CONF_LEGACY_UNIQUE_ID,
    DOMAIN,
)
from homeassistant.const import CONF_EXCLUDE, CONF_LIGHTS, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def async_step_user_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step success."""
    with patch("pyvera.VeraController") as vera_controller_class_mock:
        controller = MagicMock()
        controller.refresh_data = MagicMock()
        controller.serial_number = "serial_number_0"
        vera_controller_class_mock.return_value = controller

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["step_id"]).to_equal(config_entries.SOURCE_USER)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_CONTROLLER: "http://127.0.0.1:123/",
                CONF_LIGHTS: "12 13",
                CONF_EXCLUDE: "14 15",
            },
        )
        expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
        expect(result["title"]).to_equal("http://127.0.0.1:123")
        expect(result["data"]).to_equal(
            {
                CONF_CONTROLLER: "http://127.0.0.1:123",
                CONF_SOURCE: config_entries.SOURCE_USER,
                CONF_LIGHTS: [12, 13],
                CONF_EXCLUDE: [14, 15],
                CONF_LEGACY_UNIQUE_ID: False,
            }
        )
        expect(result["result"].unique_id).to_equal(controller.serial_number)

    entries = hass.config_entries.async_entries(DOMAIN)
    expect(bool(entries)).to_be(True)


@test
async def async_step_finish_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test finish step with error."""
    with patch("pyvera.VeraController") as vera_controller_class_mock:
        controller = MagicMock()
        controller.refresh_data = MagicMock(side_effect=RequestException())
        vera_controller_class_mock.return_value = controller

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_CONTROLLER: "http://127.0.0.1:123/"},
        )

        expect(result["type"]).to_be(FlowResultType.ABORT)
        expect(result["reason"]).to_equal("cannot_connect")
        expect(result["description_placeholders"]).to_equal(
            {"base_url": "http://127.0.0.1:123"}
        )


@test
async def options(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test updating options."""
    base_url = "http://127.0.0.1/"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=base_url,
        data={CONF_CONTROLLER: "http://127.0.0.1/"},
        options={CONF_LIGHTS: [1, 2, 3]},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(
        entry.entry_id, context={"source": "test"}, data=None
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LIGHTS: "1,2;3  4 5_6bb7",
            CONF_EXCLUDE: "8,9;10  11 12_13bb14",
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            CONF_LIGHTS: [1, 2, 3, 4, 5, 6, 7],
            CONF_EXCLUDE: [8, 9, 10, 11, 12, 13, 14],
        }
    )
