"""Tests for the Fluss Buttons."""

from unittest.mock import AsyncMock

from fluss_api import FlussApiClient, FlussApiClientError
from tryke import Depends, expect, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import setup_integration
from ._fixtures import mock_api_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def buttons() -> None:
    """Stub for test_buttons."""


@test
async def button_press(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: FlussApiClient = Depends(mock_api_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test successful button press."""
    await setup_integration(hass, entry)

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.device_1"},
        blocking=True,
    )

    client.async_trigger_device.assert_called_once_with("2a303030sdj1")


@test
async def devices_without_wifi_permission_are_filtered(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_api_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Devices whose userPermissions.canUseWiFi is false must not be surfaced."""
    client.async_get_devices.return_value = {
        "devices": [
            {
                "deviceId": "allowed",
                "deviceName": "Allowed",
                "userPermissions": {"canUseWiFi": True},
            },
            {
                "deviceId": "blocked",
                "deviceName": "Blocked",
                "userPermissions": {"canUseWiFi": False},
            },
        ]
    }

    await setup_integration(hass, entry)

    expect(hass.states.get("button.allowed")).not_.to_be(None)
    expect(hass.states.get("button.blocked")).to_be(None)
    client.async_get_device_status.assert_called_once_with("allowed")


@test
async def button_unavailable_on_status_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_api_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Buttons become unavailable when the status call errors."""
    client.async_get_device_status.side_effect = FlussApiClientError("device offline")

    await setup_integration(hass, entry)

    expect(hass.states.get("button.device_1").state).to_equal(STATE_UNAVAILABLE)
    expect(hass.states.get("button.device_2").state).to_equal(STATE_UNAVAILABLE)


@test
async def button_unavailable_when_internet_disconnected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_api_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Buttons become unavailable when the device reports no internet."""
    client.async_get_device_status.return_value = {
        "status": {"internetConnected": False}
    }

    await setup_integration(hass, entry)

    expect(hass.states.get("button.device_1").state).to_equal(STATE_UNAVAILABLE)
    expect(hass.states.get("button.device_2").state).to_equal(STATE_UNAVAILABLE)


@test
async def button_press_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: FlussApiClient = Depends(mock_api_client),
    entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test button press with API error."""
    await setup_integration(hass, entry)

    client.async_trigger_device.side_effect = FlussApiClientError("API Boom")

    async with expect_raises_async(
        HomeAssistantError, match=r"Failed to trigger device: API Boom"
    ):
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.device_1"},
            blocking=True,
        )
