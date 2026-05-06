"""Tests for the Aprilaire config flow."""

from unittest.mock import AsyncMock, Mock, patch

from pyaprilaire.client import AprilaireClient
from pyaprilaire.const import FunctionalDomain
from tryke import Depends, fixture, test

from homeassistant.components.aprilaire.config_flow import (
    STEP_USER_DATA_SCHEMA,
    AprilaireConfigFlow,
)
from homeassistant.core import HomeAssistant

from ._fixtures import client

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_input_step(_trigger: None = Depends(_trigger_executor)) -> None:
    """Test the user input step."""

    show_form_mock = Mock()

    config_flow = AprilaireConfigFlow()
    config_flow.async_show_form = show_form_mock

    await config_flow.async_step_user(None)

    show_form_mock.assert_called_once_with(
        step_id="user", data_schema=STEP_USER_DATA_SCHEMA
    )


@test
async def config_flow_invalid_data(
    _trigger: None = Depends(_trigger_executor),
    client: AprilaireClient = Depends(client),
) -> None:
    """Test that the flow is aborted with invalid data."""

    show_form_mock = Mock()
    set_unique_id_mock = AsyncMock()
    async_abort_entries_match_mock = Mock()

    config_flow = AprilaireConfigFlow()
    config_flow.async_show_form = show_form_mock
    config_flow.async_set_unique_id = set_unique_id_mock
    config_flow._async_abort_entries_match = async_abort_entries_match_mock

    with patch("pyaprilaire.client.AprilaireClient", return_value=client):
        await config_flow.async_step_user(
            {
                "host": "localhost",
                "port": 7000,
            }
        )

    client.start_listen.assert_called_once()
    client.wait_for_response.assert_called_once_with(
        FunctionalDomain.IDENTIFICATION, 2, 30
    )
    client.stop_listen.assert_called_once()

    show_form_mock.assert_called_once_with(
        step_id="user",
        data_schema=STEP_USER_DATA_SCHEMA,
        errors={"base": "connection_failed"},
    )


@test
async def config_flow_data(
    _trigger: None = Depends(_trigger_executor),
    client: AprilaireClient = Depends(client),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the config flow with valid data."""

    client.data = {"mac_address": "1:2:3:4:5:6"}

    show_form_mock = Mock()
    set_unique_id_mock = AsyncMock()
    abort_if_unique_id_configured_mock = Mock()
    create_entry_mock = Mock()

    config_flow = AprilaireConfigFlow()
    config_flow.hass = hass
    config_flow.async_show_form = show_form_mock
    config_flow.async_set_unique_id = set_unique_id_mock
    config_flow._abort_if_unique_id_configured = abort_if_unique_id_configured_mock
    config_flow.async_create_entry = create_entry_mock

    client.wait_for_response = AsyncMock(return_value={"mac_address": "1:2:3:4:5:6"})

    with patch("pyaprilaire.client.AprilaireClient", return_value=client):
        await config_flow.async_step_user(
            {
                "host": "localhost",
                "port": 7000,
            }
        )

    client.start_listen.assert_called_once()
    client.wait_for_response.assert_any_call(FunctionalDomain.CONTROL, 7, 30)
    client.wait_for_response.assert_any_call(FunctionalDomain.SENSORS, 2, 30)
    client.stop_listen.assert_called_once()

    set_unique_id_mock.assert_called_once_with("1:2:3:4:5:6")
    abort_if_unique_id_configured_mock.assert_called_once()

    create_entry_mock.assert_called_once_with(
        title="AprilAire",
        data={
            "host": "localhost",
            "port": 7000,
        },
    )
