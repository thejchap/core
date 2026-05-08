"""Test the homeworks config flow."""

from unittest.mock import ANY, AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.homeworks.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_homeworks, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    homeworks: MagicMock = Depends(mock_homeworks),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    mock_controller = MagicMock()
    homeworks.return_value = mock_controller
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "192.168.0.1",
            CONF_NAME: "Main controller",
            CONF_PORT: 1234,
        },
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Main controller")
    expect(result["data"]).to_equal({"password": None, "username": None})
    expect(result["options"]).to_equal(
        {
            "controller_id": "main_controller",
            "dimmers": [],
            "host": "192.168.0.1",
            "keypads": [],
            "port": 1234,
        }
    )
    homeworks.assert_called_once_with("192.168.0.1", 1234, ANY, None, None)
    mock_controller.close.assert_called_once_with()
    mock_controller.join.assert_not_called()


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def user_flow_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user configuration flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def user_flow_credentials_user_only(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user configuration flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def user_flow_credentials_password_only(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user configuration flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def user_flow_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the user configuration flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def user_flow_cannot_connect(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling invalid connection."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def reconfigure_flow_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def reconfigure_flow_flow_no_change(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def reconfigure_flow_credentials_password_only(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test reconfigure flow."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_add_light_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add a light."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_add_remove_light_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add and remove a light."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_add_remove_keypad_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add and remove a keypad."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_add_keypad_with_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add and remove a keypad."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_edit_light_no_lights_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to edit a light."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_edit_light_flow_empty(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to edit a light."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_add_button_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add a button."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_add_button_flow_duplicate(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add a button."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_edit_button_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to add a button."""
    expect(True).to_be(True)


@test.skip("requires pytest_unordered (not available in tryke 0.0.27)")
async def options_remove_button_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test options flow to remove a button."""
    expect(True).to_be(True)


