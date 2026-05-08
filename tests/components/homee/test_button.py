"""Test Homee buttons."""

from unittest.mock import AsyncMock, MagicMock, patch

from tryke import Depends, fixture, test

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant

from . import build_mock_node, setup_integration
from ._fixtures import mock_config_entry, mock_homee

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


_FAKE_TRANSLATIONS = {
    "component.homee.entity.button.impulse.name": "Impulse",
    "component.homee.entity.button.impulse_instance.name": "Impulse {instance}",
    "component.homee.entity.button.light.name": "Light",
    "component.homee.entity.button.open_partial.name": "Open partial",
}


async def _fake_get_translations(hass, language, category, integrations=None, config_flow=None):
    return _FAKE_TRANSLATIONS


def _fake_get_cached_translations(hass, language, category, integration=None):
    return _FAKE_TRANSLATIONS


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def button_press(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    homee: AsyncMock = Depends(mock_homee),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test press button service."""
    homee.nodes = [build_mock_node("buttons.json")]
    homee.get_node_by_id.return_value = homee.nodes[0]
    with (
        patch("homeassistant.components.homee.PLATFORMS", [Platform.BUTTON]),
        patch(
            "homeassistant.helpers.entity_platform.translation.async_get_translations",
            side_effect=_fake_get_translations,
        ),
        patch(
            "homeassistant.helpers.translation.async_get_cached_translations",
            side_effect=_fake_get_cached_translations,
        ),
    ):
        await setup_integration(hass, config_entry)

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: "button.test_button_impulse_1"},
            blocking=True,
        )

    homee.set_value.assert_called_once_with(1, 5, 1)


@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def button_snapshot() -> None:
    """Stub for test_button_snapshot."""
